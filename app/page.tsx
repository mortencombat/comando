"use client";

import Image from "next/image";
import { Power, Volume2, VolumeX } from "lucide-react";
import { Slider } from "@/components/ui/slider"
import { useState } from "react";

export default function Home() {
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(-35);

  return (
    <div className="flex items-start justify-center min-h-[100dvh] p-4 sm:p-8 bg-gradient-to-b from-slate-900 to-slate-500">
      <main className="flex flex-col gap-8 items-center sm:items-start max-w-screen-sm w-full">
        <div className="flex items-center gap-3 w-full">
          <Image
            className="dark:invert"
            src="/play.svg"
            alt="Comando logo"
            width={32}
            height={32}
            priority
          />
          <span className="text-xl font-medium">comando</span>
        </div>

        <div className="w-full bg-slate-100/5 rounded-3xl p-1">
          <div className="w-full bg-slate-100/10 rounded-3xl p-1">
            <div className="flex justify-between items-center">
              <div className="w-min rounded-3xl bg-slate-500 flex p-1 text-slate-900">
                <div className="rounded-l-3xl rounded-r-xl bg-slate-300 px-4 py-2">
                  <Image
                    className="min-w-8"
                    src="/appletv.png"
                    alt="Apple TV"
                    width={32}
                    height={32}
                  />
                </div>
                <div className="rounded-xl px-4 py-2">
                  <Image
                    className="min-w-8"
                    src="/playstation.svg"
                    alt="Playstation"
                    width={32}
                    height={32}
                  />
                </div>
                <div className="rounded-l-xl rounded-r-3xl px-4 py-3">
                  <Image
                    className="min-w-6"
                    src="/joystick.png"
                    alt="RetroPie"
                    width={32}
                    height={24}
                  />
                </div>
              </div>
              <div className="rounded-3xl bg-slate-500 h-full flex items-center p-1">
                <div className="rounded-3xl px-6 py-2">
                  <Power className="invert h-8" />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="w-full bg-slate-100/5 rounded-3xl p-1">
          <div className="w-full bg-slate-100/10 rounded-3xl p-1">
            <div className="flex justify-between items-center">
              <div className="w-min rounded-3xl bg-slate-500 flex p-1 text-slate-900">
                <div className="rounded-l-3xl rounded-r-xl bg-slate-300 px-4 py-2">
                  <Image
                    className="min-w-8"
                    src="/tv.png"
                    alt="TV"
                    width={32}
                    height={32}
                  />
                </div>
                <div className="rounded-l-xl rounded-r-3xl px-4 py-2">
                  <Image
                    className="min-w-8"
                    src="/music.png"
                    alt="Music"
                    width={32}
                    height={24}
                  />
                </div>
              </div>
              <div className="rounded-3xl bg-slate-500 h-full flex items-center p-1">
                <div className="rounded-3xl px-6 py-2">
                  <Power className="invert h-8" />
                </div>
              </div>
            </div>
          </div>
          <div className="p-4">
            <div className="flex items-center gap-4">
              <button 
                className="p-2 hover:bg-slate-100/10 rounded-full transition-colors"
                onClick={() => setIsMuted(!isMuted)}
              >
                {isMuted ? <VolumeX className="h-8 w-8" /> : <Volume2 className="h-8 w-8" />}
              </button>
              
              <div className="flex-grow">
                <Slider 
                  defaultValue={[-35]} 
                  min={-50}
                  max={-20} 
                  step={1}
                  value={[volume]}
                  onValueChange={([newValue]) => setVolume(newValue)}
                />
              </div>
              
              <span className="min-w-12 text-xl font-medium text-right">{isMuted ? '0' : volume}</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
