# encoding: utf-8
"""Glyphs reporter adapter for the pure IconGrid configuration and geometry cores."""

from __future__ import division, print_function, unicode_literals

import objc
from AppKit import NSBezierPath, NSClassFromString, NSColor, NSMakeRect
from GlyphsApp import Glyphs, MOUSEMOVED
from GlyphsApp.plugins import ReporterPlugin

from icon_grid.config import resolve_config
from icon_grid.geometry import build_geometry, hit_test_guides, line_width_for_scale
from icon_grid.runtime import (
	parameter_entries,
	resolve_layer_context,
	resolve_mouse_context,
	tool_allows_drawing,
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


class GlyphsIconGrid(ReporterPlugin):

	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({"en": "Icon Grid"})
		self._warned_messages = set()
		self._mouse_callback = None
		self._hover_layer = None
		self._hover_point = None
		self._hover_hits = ()

	def willActivate(self):
		if self._mouse_callback is not None:
			return
		self._mouse_callback = self._mouse_moved
		Glyphs.addCallback(self._mouse_callback, MOUSEMOVED)

	def willDeactivate(self):
		if self._mouse_callback is not None:
			Glyphs.removeCallback(self._mouse_callback, MOUSEMOVED)
			self._mouse_callback = None
		self._hover_layer = None
		self._hover_point = None
		self._hover_hits = ()

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
		)
		for warning in warnings:
			self._warn_once(warning)
		geometry = build_geometry(context.width, config)
		if geometry is None:
			return None
		return config, geometry

	@objc.python_method
	def _set_hover(self, layer, point, hits):
		visual_change = hits != self._hover_hits or (
			bool(hits) and layer is not self._hover_layer
		)
		self._hover_layer = layer
		self._hover_point = point
		self._hover_hits = hits
		if visual_change:
			Glyphs.redraw()

	@objc.python_method
	def _mouse_moved(self, _notification):
		event_getter = getattr(Glyphs, "currentEvent", None)
		event = event_getter() if callable(event_getter) else None
		mouse = resolve_mouse_context(getattr(self, "controller", None), event)
		if mouse is None or not tool_allows_drawing(
			getattr(self, "controller", None), NSClassFromString
		):
			self._set_hover(None, None, ())
			return

		resolved = self._geometry_for_layer(mouse.layer)
		if resolved is None:
			self._set_hover(None, None, ())
			return
		config, geometry = resolved
		hits = ()
		if config.hover_highlight:
			hits = hit_test_guides(
				geometry,
				mouse.point,
				config.hover_tolerance / mouse.scale,
			)
		self._set_hover(mouse.layer, mouse.point, hits)

	@objc.python_method
	def background(self, layer):
		if not tool_allows_drawing(getattr(self, "controller", None), NSClassFromString):
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

		hover_hits = ()
		if (
			config.hover_highlight
			and self._hover_layer is layer
			and self._hover_point is not None
		):
			hover_hits = hit_test_guides(
				geometry,
				self._hover_point,
				config.hover_tolerance / scale,
			)
			self._hover_hits = hover_hits
		if hover_hits:
			_stroke(
				_highlight_path(geometry, hover_hits),
				color,
				min(1.0, config.opacity * 2.5),
				2.0,
				scale,
			)
		return None

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
