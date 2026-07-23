# encoding: utf-8
"""Glyphs reporter adapter for the pure IconGrid configuration and geometry cores."""

from __future__ import division, print_function, unicode_literals

import objc
from AppKit import NSBezierPath, NSClassFromString, NSColor, NSMakeRect
from GlyphsApp import Glyphs, MOUSEMOVED
from GlyphsApp.plugins import ReporterPlugin

from glyphs_icon_grid.config import resolve_config
from glyphs_icon_grid.geometry import build_geometry, hit_test_guides, line_width_for_scale
from glyphs_icon_grid.runtime import (
	active_mouse_context,
	parameter_entries,
	resolve_layer_context,
	selected_node_records,
	tool_allows_drawing,
	tool_creation_drag_point,
	tool_drag_session,
	tool_is_annotation,
	tool_is_drawing,
	tool_uses_creation_hover,
)


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


def _alignment_hits(geometry, points, tolerance):
	hits = []
	seen = set()
	for point in points:
		for reference in hit_test_guides(geometry, point, tolerance):
			if reference in seen:
				continue
			hits.append(reference)
			seen.add(reference)
	return tuple(hits)


def _same_object(left, right):
	if left is right:
		return True
	try:
		return bool(left == right)
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

	@objc.python_method
	def __del__(self):
		try:
			if getattr(self, "_creation_hover_callback_registered", False):
				Glyphs.removeCallback(self._mouse_moved, MOUSEMOVED)
		except Exception:
			pass

	@objc.python_method
	def _mouse_moved(self, notification):
		controller = _controller(self)
		if not tool_uses_creation_hover(controller, NSClassFromString):
			had_hover = self._creation_hover_point is not None
			self._creation_hover_layer = None
			self._creation_hover_point = None
			if had_hover:
				Glyphs.redraw()
			return

		context = active_mouse_context(controller, notification)
		if context is None:
			if self._creation_hover_point is None:
				return
			self._creation_hover_layer = None
			self._creation_hover_point = None
		else:
			layer, point = context
			if (
				_same_object(layer, self._creation_hover_layer)
				and point == self._creation_hover_point
			):
				return
			self._creation_hover_layer = layer
			self._creation_hover_point = point
		Glyphs.redraw()

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
			return None
		resolved = self._geometry_for_layer(layer)
		if resolved is None:
			return None
		config, geometry = resolved

		color = _base_color(config.color)
		scale = self.getScale()
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
		active_drag = tool_drag_session(controller) is not None
		if active_drag and tool_uses_creation_hover(controller, NSClassFromString):
			self._creation_hover_layer = None
			self._creation_hover_point = None
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
		alignment_hits = ()
		if config.alignment_highlight and alignment_points:
			alignment_hits = _alignment_hits(
				geometry,
				alignment_points,
				config.alignment_tolerance / scale,
			)
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
