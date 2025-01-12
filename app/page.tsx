import Image from "next/image";

export default function Home() {
  return (
    <div className="flex items-start justify-center min-h-[100dvh] p-4 sm:p-8">
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

        <div className="w-full bg-slate-500/20 rounded-3xl p-8">
          <p><strong>Video</strong></p>
          <p>Some controls here.</p>
        </div>
        <div className="w-full bg-slate-500/20 rounded-3xl p-8">
          <p><strong>Audio</strong></p>
          <p>Some controls here.</p>
        </div>
      </main>
    </div>
  );
}
