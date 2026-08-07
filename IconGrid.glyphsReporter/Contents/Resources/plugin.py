# encoding: utf-8
"""Glyphs reporter adapter for the pure IconGrid configuration and geometry cores."""

from __future__ import division, print_function, unicode_literals

import math

import objc
from AppKit import NSBezierPath, NSClassFromString, NSColor, NSMakeRect
from GlyphsApp import Glyphs, GSMetricsTypeMidHeight, MOUSEMOVED
from GlyphsApp.plugins import ReporterPlugin

from glyphs_icon_grid.config import resolve_config
from glyphs_icon_grid.geometry import (
	build_geometry,
	build_guide_catalog,
	hit_test_guide_catalog,
	line_width_for_scale,
)
from glyphs_icon_grid.runtime import (
	active_mouse_context,
	master_metric_position,
	parameter_entries,
	preferred_master_stem,
	resolve_layer_context,
	selected_node_records,
	tool_allows_drawing,
	tool_creation_drag_point,
	tool_drag_session,
	tool_is_annotation,
	tool_is_drawing,
	tool_uses_creation_hover,
)


_MAX_ALIGNMENT_POINTS = 64


def _rect(canvas):
	return NSMakeRect(canvas.xmin, canvas.ymin, canvas.width, canvas.height)


def _line_path(lines):
	path = NSBezierPath.bezierPath()
	for line in lines:
		path.moveToPoint_((line.x1, line.y1))
		path.lineToPoint_((line.x2, line.y2))
	return path


def _frame_path(frames):
	path = NSBezierPath.bezierPath()
	for frame in frames:
		path.appendBezierPathWithRect_(_rect(frame))
	return path


def _ring_path(rings):
	path = NSBezierPath.bezierPath()
	for ring in rings:
		path.appendBezierPathWithOvalInRect_(
			NSMakeRect(
				ring.cx - ring.radius,
				ring.cy - ring.radius,
				ring.radius * 2.0,
				ring.radius * 2.0,
			)
		)
	return path


def _keyline_path(keylines):
	path = NSBezierPath.bezierPath()
	for keyline in keylines:
		keyline_rect = NSMakeRect(keyline.x, keyline.y, keyline.width, keyline.height)
		if keyline.shape == "circle":
			path.appendBezierPathWithOvalInRect_(keyline_rect)
		else:
			path.appendBezierPathWithRect_(keyline_rect)
	return path


def _highlight_path(geometry, references):
	path = NSBezierPath.bezierPath()
	collections = {
		"minor": geometry.minor_lines,
		"major": geometry.major_lines,
		"axis": geometry.axis_lines,
		"frame": geometry.frames,
		"ring": geometry.rings,
		"spoke": geometry.spokes,
		"keyline": geometry.keylines,
	}
	for reference in references:
		items = collections.get(reference.kind, ())
		if reference.index < 0 or reference.index >= len(items):
			continue
		item = items[reference.index]
		if reference.kind in ("minor", "major", "axis", "spoke"):
			path.moveToPoint_((item.x1, item.y1))
			path.lineToPoint_((item.x2, item.y2))
		elif reference.kind == "frame":
			path.appendBezierPathWithRect_(_rect(item))
		elif reference.kind == "ring":
			path.appendBezierPathWithOvalInRect_(
				NSMakeRect(
					item.cx - item.radius,
					item.cy - item.radius,
					item.radius * 2.0,
					item.radius * 2.0,
				)
			)
		elif reference.kind == "keyline":
			item_rect = NSMakeRect(item.x, item.y, item.width, item.height)
			if item.shape == "circle":
				path.appendBezierPathWithOvalInRect_(item_rect)
			else:
				path.appendBezierPathWithRect_(item_rect)
	return path


def _base_color(color):
	if isinstance(color, tuple):
		return NSColor.colorWithCalibratedRed_green_blue_alpha_(
			color[0], color[1], color[2], 1.0
		)
	selectors = {
		"accent": "controlAccentColor",
		"grid": "gridColor",
		"label": "labelColor",
		"separator": "separatorColor",
	}
	semantic_color = getattr(NSColor, selectors.get(color, "controlAccentColor"), None)
	if callable(semantic_color):
		return semantic_color()
	return NSColor.gridColor()


def _stroke(path, color, opacity, screen_pixels, scale):
	color.colorWithAlphaComponent_(opacity).set()
	path.setLineWidth_(line_width_for_scale(screen_pixels, scale))
	path.stroke()


def _controller(plugin):
	controller = getattr(plugin, "controller", None)
	try:
		return controller() if callable(controller) else controller
	except (AttributeError, TypeError):
		return None


def _alignment_hits(catalog, points, tolerance):
	return hit_test_guide_catalog(
		catalog,
		points,
		tolerance,
		max_points=_MAX_ALIGNMENT_POINTS,
	)


def _same_object(left, right):
	if left is right:
		return True
	try:
		return bool(left == right)
	except Exception:
		return False


def _positive_scale(value):
	try:
		scale = float(value)
	except (TypeError, ValueError, OverflowError):
		return None
	if not math.isfinite(scale) or scale <= 0:
		return None
	return scale


def _graphic_view(controller):
	if controller is None:
		return None
	try:
		view = getattr(controller, "graphicView")
		return view() if callable(view) else view
	except Exception:
		return None


def _invalidate_edit_view(controller):
	view = _graphic_view(controller)
	if view is None:
		return False
	try:
		invalidate = getattr(view, "setNeedsDisplay_")
		if not callable(invalidate):
			return False
		invalidate(True)
		return True
	except Exception:
		return False


class GlyphsIconGridReporter(ReporterPlugin):

	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({"en": "Icon Grid"})
		self._warned_messages = set()
		self._alignment_layer = None
		self._alignment_idle_nodes = {}
		self._alignment_drag_nodes = {}
		self._alignment_moving_nodes = set()
		self._alignment_drag_session = None
		self._creation_hover_layer = None
		self._creation_hover_point = None
		self._creation_hover_hits = ()
		self._hover_render_cache = None
		self._creation_hover_callback_registered = False

	def willActivate(self):
		if self._creation_hover_callback_registered:
			return
		Glyphs.addCallback(self._mouse_moved, MOUSEMOVED)
		self._creation_hover_callback_registered = True

	def willDeactivate(self):
		if self._creation_hover_callback_registered:
			Glyphs.removeCallback(self._mouse_moved, MOUSEMOVED)
		self._creation_hover_callback_registered = False
		self._creation_hover_layer = None
		self._creation_hover_point = None
		self._creation_hover_hits = ()
		self._hover_render_cache = None

	@objc.python_method
	def __del__(self):
		try:
			if getattr(self, "_creation_hover_callback_registered", False):
				Glyphs.removeCallback(self._mouse_moved, MOUSEMOVED)
		except Exception:
			pass

	@objc.python_method
	def _set_creation_hover(self, controller, layer, point, hits, invalidate=True):
		visual_change = hits != self._creation_hover_hits or (
			bool(hits) and not _same_object(layer, self._creation_hover_layer)
		)
		self._creation_hover_layer = layer
		self._creation_hover_point = point
		self._creation_hover_hits = hits
		if invalidate and visual_change:
			_invalidate_edit_view(controller)

	@objc.python_method
	def _cache_hover_render(self, layer, config, geometry, scale):
		scale = _positive_scale(scale)
		if scale is None:
			self._hover_render_cache = None
			return None
		catalog = build_guide_catalog(geometry)
		self._hover_render_cache = (layer, config, geometry, catalog, scale)
		return catalog, scale

	@objc.python_method
	def _cached_hover_render(self, layer):
		cache = self._hover_render_cache
		if cache is None or not _same_object(layer, cache[0]):
			return None
		return cache

	@objc.python_method
	def _mouse_moved(self, notification):
		controller = None
		try:
			controller = _controller(self)
			self._handle_mouse_moved(controller, notification)
		except Exception as error:
			self._set_creation_hover(controller, None, None, ())
			try:
				self._warn_once(
					"Hover callback ignored an unexpected {}.".format(
						error.__class__.__name__
					)
				)
			except Exception:
				pass

	@objc.python_method
	def _handle_mouse_moved(self, controller, notification):
		if tool_drag_session(controller) is not None:
			# Glyphs owns the live primitive preview while dragging. Reporter
			# invalidation here can erase that overlay before the tool presents it.
			self._set_creation_hover(
				controller,
				None,
				None,
				(),
				invalidate=False,
			)
			return
		if not tool_uses_creation_hover(controller, NSClassFromString):
			self._set_creation_hover(controller, None, None, ())
			return

		context = active_mouse_context(controller, notification)
		if context is None:
			self._set_creation_hover(controller, None, None, ())
			return

		layer, point = context
		if (
			_same_object(layer, self._creation_hover_layer)
			and point == self._creation_hover_point
		):
			return

		hits = ()
		cache = self._cached_hover_render(layer)
		if cache is not None:
			_layer, config, _geometry, catalog, scale = cache
			if config.alignment_highlight:
				hits = _alignment_hits(
					catalog,
					(point,),
					config.alignment_tolerance / scale,
				)
		self._set_creation_hover(controller, layer, point, hits)

	@objc.python_method
	def _warn_once(self, message):
		if message in self._warned_messages:
			return
		self._warned_messages.add(message)
		logger = getattr(self, "logToConsole", None)
		if callable(logger):
			logger("IconGrid: {}".format(message))
		else:
			print("IconGrid: {}".format(message))

	@objc.python_method
	def _geometry_for_layer(self, layer):
		context = resolve_layer_context(layer)
		if context is None:
			return None
		config, warnings = resolve_config(
			parameter_entries(context.font),
			parameter_entries(context.master),
			getattr(context.master, "capHeight", None),
			getattr(context.font, "upm", None),
			master_x_height=getattr(context.master, "xHeight", None),
			master_ascender=getattr(context.master, "ascender", None),
			master_descender=getattr(context.master, "descender", None),
			master_stem=preferred_master_stem(context.font, context.master),
			master_mid_height=master_metric_position(
				context.font,
				context.master,
				GSMetricsTypeMidHeight,
			),
		)
		for warning in warnings:
			self._warn_once(warning)
		geometry = build_geometry(context.width, config)
		if geometry is None:
			return None
		return config, geometry

	@objc.python_method
	def _moving_node_points(self, layer, controller):
		"""Track real node edits without observing passive pointer movement."""

		current = dict(selected_node_records(layer, NSClassFromString))
		if tool_is_annotation(controller, NSClassFromString):
			self._alignment_layer = layer
			self._alignment_idle_nodes = current
			self._alignment_drag_nodes = {}
			self._alignment_moving_nodes = set()
			self._alignment_drag_session = None
			return ()
		drag_session = tool_drag_session(controller)
		dragging = drag_session is not None

		if layer != self._alignment_layer:
			self._alignment_layer = layer
			self._alignment_idle_nodes = {} if dragging else current
			self._alignment_drag_nodes = {}
			self._alignment_moving_nodes = set()
			self._alignment_drag_session = None

		if not dragging:
			self._alignment_idle_nodes = current
			self._alignment_drag_nodes = {}
			self._alignment_moving_nodes = set()
			self._alignment_drag_session = None
			return ()

		if drag_session != self._alignment_drag_session:
			if self._alignment_drag_session is not None:
				self._alignment_idle_nodes = self._alignment_drag_nodes
			self._alignment_drag_nodes = {}
			self._alignment_moving_nodes = set()
			self._alignment_drag_session = drag_session

		moved_from_idle = {
			node
			for node, point in current.items()
			if (
			node in self._alignment_idle_nodes
			and self._alignment_idle_nodes[node] != point
			)
		}
		moved_during_drag = {
			node
			for node, point in current.items()
			if (
			node in self._alignment_drag_nodes
			and self._alignment_drag_nodes[node] != point
			)
		}
		added_by_draw_tool = set()
		if tool_is_drawing(controller, NSClassFromString):
			added_by_draw_tool = {
				node for node in current if node not in self._alignment_idle_nodes
			}

		self._alignment_moving_nodes.update(
			moved_from_idle | moved_during_drag | added_by_draw_tool
		)
		self._alignment_drag_nodes = current

		if not self._alignment_moving_nodes:
			return ()
		return tuple(
			dict.fromkeys(
				point
				for node, point in current.items()
				if node in self._alignment_moving_nodes
			)
		)

	@objc.python_method
	def background(self, layer):
		controller = _controller(self)
		if not tool_allows_drawing(controller, NSClassFromString):
			self._hover_render_cache = None
			return None
		resolved = self._geometry_for_layer(layer)
		if resolved is None:
			self._hover_render_cache = None
			return None
		config, geometry = resolved

		color = _base_color(config.color)
		scale = self.getScale()
		hover_render = self._cache_hover_render(layer, config, geometry, scale)
		if hover_render is None:
			guide_catalog = ()
			hover_scale = None
		else:
			guide_catalog, hover_scale = hover_render
		if geometry.minor_lines:
			_stroke(_line_path(geometry.minor_lines), color, config.opacity * 0.45, 0.55, scale)
		if geometry.spokes:
			_stroke(_line_path(geometry.spokes), color, config.opacity * 0.55, 0.65, scale)
		if geometry.rings:
			_stroke(_ring_path(geometry.rings), color, config.opacity * 0.65, 0.75, scale)
		if geometry.major_lines:
			_stroke(_line_path(geometry.major_lines), color, config.opacity * 0.8, 0.9, scale)
		if geometry.axis_lines:
			_stroke(_line_path(geometry.axis_lines), color, config.opacity, 1.2, scale)
		if geometry.frames:
			_stroke(_frame_path(geometry.frames), color, config.opacity, 1.0, scale)
		if geometry.keylines:
			_stroke(_keyline_path(geometry.keylines), color, config.opacity * 0.9, 1.0, scale)

		moving_node_points = self._moving_node_points(layer, controller)
		alignment_points = moving_node_points
		using_creation_hover = False
		active_drag = tool_drag_session(controller) is not None
		if active_drag and tool_uses_creation_hover(controller, NSClassFromString):
			self._creation_hover_layer = None
			self._creation_hover_point = None
			self._creation_hover_hits = ()
		if not alignment_points:
			creation_point = tool_creation_drag_point(
				controller,
				NSClassFromString,
			)
			if creation_point is not None:
				alignment_points = (creation_point,)
		if (
			not alignment_points
			and not active_drag
			and tool_uses_creation_hover(controller, NSClassFromString)
			and self._creation_hover_point is not None
			and _same_object(layer, self._creation_hover_layer)
		):
			alignment_points = (self._creation_hover_point,)
			using_creation_hover = True
		alignment_hits = ()
		if (
			config.alignment_highlight
			and alignment_points
			and hover_scale is not None
		):
			alignment_hits = _alignment_hits(
				guide_catalog,
				alignment_points,
				config.alignment_tolerance / hover_scale,
			)
		if using_creation_hover:
			self._creation_hover_hits = alignment_hits
		if alignment_hits:
			_stroke(
				_highlight_path(geometry, alignment_hits),
				color,
				min(1.0, config.opacity * 1.6),
				1.4,
				scale,
			)
		return None

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
