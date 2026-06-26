"use client";

import { useEffect, useMemo, useState } from "react";

type Project = {
  title: string;
  tag: string;
  description: string;
  href?: string;
};

const projects: Project[] = [
  {
    title: "MedSignal AI",
    tag: "Healthcare intelligence",
    description:
      "A medication safety dashboard that turns FDA labels and adverse event data into searchable risk signals.",
    href: "/medsignal-ai",
  },
  {
    title: "Signal Studio",
    tag: "Product design",
    description:
      "A compact workspace for reviewing trends, exporting summaries, and moving from raw data to decisions.",
  },
  {
    title: "Portfolio Engine",
    tag: "Interactive web",
    description:
      "A scroll-led personal site with cinematic scenes, precise motion, and fast Next.js rendering.",
  },
];

const capabilities = [
  "Next.js",
  "React",
  "TypeScript",
  "Tailwind CSS",
  "Python",
  "FastAPI",
  "Data pipelines",
  "UI systems",
];

export default function Home() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const updateProgress = () => {
      const scrollable =
        document.documentElement.scrollHeight - window.innerHeight;
      setProgress(scrollable > 0 ? window.scrollY / scrollable : 0);
    };

    updateProgress();
    window.addEventListener("scroll", updateProgress, { passive: true });
    window.addEventListener("resize", updateProgress);

    return () => {
      window.removeEventListener("scroll", updateProgress);
      window.removeEventListener("resize", updateProgress);
    };
  }, []);

  const activeScene = useMemo(() => {
    if (progress < 0.28) return "origin";
    if (progress < 0.58) return "work";
    if (progress < 0.82) return "craft";
    return "contact";
  }, [progress]);

  return (
    <main
      className="portfolio-shell min-h-screen overflow-hidden text-white"
      style={{ "--scroll-progress": progress } as React.CSSProperties}
    >
      <CinematicScene progress={progress} activeScene={activeScene} />

      <nav className="fixed left-0 right-0 top-0 z-30 border-b border-white/10 bg-black/20 px-5 py-4 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4">
          <a className="text-sm font-semibold uppercase text-white" href="#top">
            Yeshas Krishna
          </a>
          <div className="hidden items-center gap-6 text-sm text-white/70 sm:flex">
            <a className="transition hover:text-white" href="#work">
              Work
            </a>
            <a className="transition hover:text-white" href="#craft">
              Craft
            </a>
            <a className="transition hover:text-white" href="#contact">
              Contact
            </a>
          </div>
        </div>
      </nav>

      <section
        id="top"
        className="relative z-10 flex min-h-screen items-end px-5 pb-16 pt-28 sm:items-center sm:pb-24"
      >
        <div className="mx-auto grid w-full max-w-6xl gap-10 lg:grid-cols-[1fr_360px] lg:items-end">
          <div className="max-w-4xl">
            <p className="mb-5 max-w-max border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium uppercase text-white/80 backdrop-blur-md">
              Developer portfolio
            </p>
            <h1 className="max-w-5xl text-5xl font-semibold leading-none text-white sm:text-7xl lg:text-8xl">
              Scroll through the work like a trailer.
            </h1>
            <p className="mt-7 max-w-2xl text-lg leading-8 text-white/74 sm:text-xl">
              I build healthcare tools, polished interfaces, and data-heavy
              products that feel fast, cinematic, and useful from the first
              click.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <a
                className="inline-flex min-h-12 items-center justify-center border border-white bg-white px-5 text-sm font-semibold text-black transition hover:bg-transparent hover:text-white"
                href="#work"
              >
                View selected work
              </a>
              <a
                className="inline-flex min-h-12 items-center justify-center border border-white/20 bg-white/10 px-5 text-sm font-semibold text-white transition hover:border-white hover:bg-white/15"
                href="#contact"
              >
                Start a conversation
              </a>
            </div>
          </div>

          <div className="status-panel border border-white/14 bg-black/28 p-5 backdrop-blur-xl">
            <div className="flex items-center justify-between text-sm text-white/65">
              <span>Current scene</span>
              <span className="capitalize text-white">{activeScene}</span>
            </div>
            <div className="mt-5 h-2 overflow-hidden bg-white/12">
              <div
                className="h-full bg-[#7fffd4] transition-[width] duration-150"
                style={{ width: `${Math.round(progress * 100)}%` }}
              />
            </div>
            <p className="mt-5 text-sm leading-6 text-white/70">
              The background reacts to scroll position: color, depth, light,
              and perspective shift as each portfolio chapter comes into view.
            </p>
          </div>
        </div>
      </section>

      <section id="work" className="relative z-10 px-5 py-28 sm:py-36">
        <div className="mx-auto max-w-6xl">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase text-[#7fffd4]">
              Selected work
            </p>
            <h2 className="mt-4 text-4xl font-semibold leading-tight sm:text-6xl">
              Product moments with real systems behind them.
            </h2>
          </div>

          <div className="mt-12 grid gap-4 md:grid-cols-3">
            {projects.map((project, index) => (
              <article
                className="project-tile min-h-[330px] border border-white/14 bg-white/[0.08] p-6 backdrop-blur-xl"
                key={project.title}
              >
                <div className="flex h-full flex-col justify-between">
                  <div>
                    <div className="mb-8 flex items-center justify-between text-sm text-white/55">
                      <span>{project.tag}</span>
                      <span>0{index + 1}</span>
                    </div>
                    <h3 className="text-2xl font-semibold text-white">
                      {project.title}
                    </h3>
                    <p className="mt-5 text-base leading-7 text-white/68">
                      {project.description}
                    </p>
                  </div>
                  <div className="mt-10">
                    {project.href ? (
                      <a
                        className="inline-flex min-h-11 items-center border border-white/30 px-4 text-sm font-semibold text-white transition hover:border-white hover:bg-white hover:text-black"
                        href={project.href}
                      >
                        Launch app
                        <span aria-hidden="true" className="ml-2">
                          &rarr;
                        </span>
                      </a>
                    ) : (
                      <div className="h-1 w-full bg-white/12">
                        <div className="h-full w-2/3 bg-[#ff7a5c]" />
                      </div>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="craft" className="relative z-10 px-5 py-28 sm:py-36">
        <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
          <div className="sticky top-28">
            <p className="text-sm font-semibold uppercase text-[#ffd166]">
              Craft
            </p>
            <h2 className="mt-4 text-4xl font-semibold leading-tight sm:text-6xl">
              Clean code, sharp visuals, clear product thinking.
            </h2>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {capabilities.map((item) => (
              <div
                className="flex min-h-24 items-center border border-white/14 bg-black/28 px-5 text-lg font-semibold text-white backdrop-blur-xl"
                key={item}
              >
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="contact" className="relative z-10 px-5 py-28 sm:py-36">
        <div className="mx-auto max-w-6xl border-t border-white/16 pt-12">
          <p className="text-sm font-semibold uppercase text-[#7fffd4]">
            Contact
          </p>
          <div className="mt-5 grid gap-8 lg:grid-cols-[1fr_340px] lg:items-end">
            <h2 className="max-w-4xl text-4xl font-semibold leading-tight sm:text-6xl">
              Have a product idea, dashboard, or portfolio upgrade in mind?
            </h2>
            <div>
              <a
                className="inline-flex min-h-12 w-full items-center justify-center border border-white bg-white px-5 text-sm font-semibold text-black transition hover:bg-transparent hover:text-white"
                href="mailto:yeshas@example.com"
              >
                yeshas@example.com
              </a>
              <p className="mt-5 text-sm leading-6 text-white/60">
                Replace this email, project copy, and links with your real
                details when you are ready to personalize it fully.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

function CinematicScene({
  progress,
  activeScene,
}: {
  progress: number;
  activeScene: string;
}) {
  const depth = progress * 100;

  return (
    <div className={`scene scene-${activeScene}`} aria-hidden="true">
      <div className="scene-sky" />
      <div
        className="scene-track"
        style={{
          transform: `translate3d(0, ${depth * -1.2}px, 0) rotateX(${58 - progress * 20}deg)`,
        }}
      >
        {Array.from({ length: 18 }).map((_, index) => (
          <span
            className="track-line"
            key={index}
            style={{ left: `${index * 6}%` }}
          />
        ))}
        {Array.from({ length: 16 }).map((_, index) => (
          <span
            className="track-cross"
            key={index}
            style={{ top: `${index * 8}%` }}
          />
        ))}
      </div>
      <div
        className="glass-slab slab-one"
        style={{ transform: `translateY(${progress * -80}px) rotate(-8deg)` }}
      />
      <div
        className="glass-slab slab-two"
        style={{ transform: `translateY(${progress * 140}px) rotate(12deg)` }}
      />
      <div
        className="light-ribbon"
        style={{ transform: `translateX(${progress * 30}px) skewX(-18deg)` }}
      />
      <div className="grain" />
    </div>
  );
}
