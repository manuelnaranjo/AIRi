package com.flashdynamix.utils {
	import flash.display.*;
	import flash.events.*;
	import flash.net.LocalConnection;
	import flash.system.System;
	import flash.ui.*;
	import flash.utils.getTimer;

	import net.aircable.XHRMultipartEvent;
	import net.aircable.XHRMultipart;

	/**
	 * @author shanem
	 */
	public class SWFProfiler {
		private static var itvTime : int;
		private static var initTime : int;
		private static var currentTime : int;
		private static var frameCount : int;
		private static var totalCount : int;

		public static var minFps : Number;
		public static var maxFps : Number;
		public static var minMem : Number;
		public static var maxMem : Number;
		public static var history : int = 60;
		public static var fpsList : Array = [];
		public static var memList : Array = [];

		private static var displayed : Boolean = false;
		private static var started : Boolean = false;
		private static var inited : Boolean = false;
		private static var frame : Sprite;
		private static var stage : Stage;
		private static var content : ProfilerContent;
		private static var ci : ContextMenuItem;
		private static var socket : XHRMultipart;

		public static function init(swf : Stage, context : InteractiveObject, sock: XHRMultipart) : void {
			socket = sock;
			if(inited) return;
			
			inited = true;
			stage = swf;
			
			content = new ProfilerContent();
			frame = new Sprite();
			
			minFps = Number.MAX_VALUE;
			maxFps = Number.MIN_VALUE;
			minMem = Number.MAX_VALUE;
			maxMem = Number.MIN_VALUE;
			
			var cm : ContextMenu = new ContextMenu();
			cm.hideBuiltInItems();
			ci = new ContextMenuItem("Show Profiler", true);
			addEvent(ci, ContextMenuEvent.MENU_ITEM_SELECT, onSelect);
			cm.customItems = [ci];
			context.contextMenu = cm;
			
			start();
			show();
		}

		public static function start() : void {
			if(started) return;
			
			started = true;
			initTime = itvTime = getTimer();
			totalCount = frameCount = 0;
			
			addEvent(socket, XHRMultipartEvent.GOT_DATA, draw);
		}

		public static function stop() : void {
			if(!started) return;
			
			started = false;
			
			removeEvent(frame, Event.ENTER_FRAME, draw);
		}

		public static function gc() : void {
			try {
				new LocalConnection().connect('foo');
				new LocalConnection().connect('foo');
			} catch (e : Error) {
			}
		}

		public static function get currentFps() : Number {
			return frameCount / intervalTime;
		}

		public static function get currentMem() : Number {
			return (System.totalMemory / 1024) / 1000;
		}

		public static function get averageFps() : Number {
			return totalCount / runningTime;
		}

		private static function get runningTime() : Number {
			return (currentTime - initTime) / 1000;
		}

		private static function get intervalTime() : Number {
			return (currentTime - itvTime) / 1000;
		}

		
		private static function onSelect(e : ContextMenuEvent) : void {
			if(!displayed) {
				show();
			} else {
				hide();
			}
		}

		private static function show() : void {
			ci.caption = "Hide Profiler";
			displayed = true;
			addEvent(stage, Event.RESIZE, resize);
			stage.addChild(content);
			updateDisplay();
		}

		private static function hide() : void {
			ci.caption = "Show Profiler";
			displayed = false;
			removeEvent(stage, Event.RESIZE, resize);
			stage.removeChild(content);
		}
		
		private static function resize(e:Event) : void {
			content.update(runningTime, minFps, maxFps, minMem, maxMem, currentFps, currentMem, averageFps, fpsList, memList, history);
		}
		
		private static function draw(e : Event) : void {
			currentTime = getTimer();
			
			frameCount++;
			totalCount++;

			if(intervalTime >= 1) {
				if(displayed) {
					updateDisplay();
				} else {
					updateMinMax();
				}
				
				fpsList.unshift(currentFps);
				memList.unshift(currentMem);
				
				if(fpsList.length > history) fpsList.pop();
				if(memList.length > history) memList.pop();
				
				itvTime = currentTime;
				frameCount = 0;
			}
		}

		private static function updateDisplay() : void {
			updateMinMax();
			content.update(runningTime, minFps, maxFps, minMem, maxMem, currentFps, currentMem, averageFps, fpsList, memList, history);
		}

		private static function updateMinMax() : void {
			minFps = Math.min(currentFps, minFps);
			maxFps = Math.max(currentFps, maxFps);
				
			minMem = Math.min(currentMem, minMem);
			maxMem = Math.max(currentMem, maxMem);
		}

		private static function addEvent(item : EventDispatcher, type : String, listener : Function) : void {
			item.addEventListener(type, listener, false, 0, true);
		}

		private static function removeEvent(item : EventDispatcher, type : String, listener : Function) : void {
			item.removeEventListener(type, listener);
		}
	}
}

import flash.display.*;
import flash.events.Event;
import flash.text.*;

internal class ProfilerContent extends Sprite {

	private var infoTxtBx : TextField;

	public function ProfilerContent() : void {
		this.mouseChildren = false;
		this.mouseEnabled = false;

		infoTxtBx = new TextField();
		infoTxtBx.autoSize = TextFieldAutoSize.LEFT;
		infoTxtBx.defaultTextFormat = new TextFormat("_sans", 8, 0x0000000);
		infoTxtBx.x = 0;
		infoTxtBx.y = 0;

		addChild(infoTxtBx);
	}

	public function update(runningTime : Number, minFps : Number, maxFps : Number, minMem : Number, maxMem : Number, currentFps : Number, currentMem : Number, averageFps : Number, fpsList : Array, memList : Array, history : int) : void {
		infoTxtBx.text = "Current Fps " + currentFps.toFixed(3) + "   |   Average Fps " + averageFps.toFixed(3) + "   |   Memory Used " + currentMem.toFixed(3) + " Mb";
	}

}