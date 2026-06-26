"use client";

import { useEffect, useMemo, useState } from "react";

type Project = {
  title: string;
  tag: string;
  stack: string;
  description: string;
};

type Experience = {
  role: string;
  organization: string;
  dates: string;
  location: string;
  logo: string;
  impact: string;
};

type LogoItem = {
  name: string;
  src: string;
};

const projects: Project[] = [
  {
    title: "Collabo",
    tag: "Collaborative code editor",
    stack: "React, Next.js, Monaco, Yjs, WebRTC, Render, Piston API",
    description:
      "A real-time code editor where multiple users can edit one document together, sync versions, and run code securely in the browser.",
  },
  {
    title: "QuizLo.ai",
    tag: "Adaptive quiz platform",
    stack: "Next.js, Node/Express, MongoDB Atlas, Google Gemini, RAG",
    description:
      "An AI quiz platform that generates context-aware questions and adjusts difficulty based on each student's performance.",
  },
  {
    title: "Quality Assurance Dashboard",
    tag: "Healthcare education platform",
    stack: "React, .NET, SQL, Azure",
    description:
      "A production dashboard for 1,000+ students to submit lab results, with monitoring, automated error handling, and grading workflow improvements.",
  },
];

const experiences: Experience[] = [
  {
    role: "Software Engineer",
    organization: "TTU Health Sciences Center",
    dates: "Aug 2024 - Dec 2024",
    location: "Lubbock, TX",
    logo: "https://commons.wikimedia.org/wiki/Special:FilePath/Texas%20Tech%20University%20Health%20Sciences%20Center%20logo.svg",
    impact:
      "Built and deployed a React/.NET dashboard on Azure, shipped 10+ user-driven enhancements, and helped reduce manual review time by 30%.",
  },
  {
    role: "Teaching Assistant",
    organization: "Texas Tech University",
    dates: "Aug 2024 - May 2025",
    location: "Lubbock, TX",
    logo: "https://commons.wikimedia.org/wiki/Special:FilePath/Texas%20Tech%20New%20Logo.svg",
    impact:
      "Led live-coding sessions and weekly reviews for Data Structures, Algorithms, and OOP, helping increase pass rates by 35%.",
  },
  {
    role: "Student Outreach Director",
    organization: "Texas Society of Professional Engineers",
    dates: "Sep 2023 - Present",
    location: "Texas Tech University",
    logo: "https://commons.wikimedia.org/wiki/Special:FilePath/Texas%20Tech%20New%20Logo.svg",
    impact:
      "Built industry partnerships, organized outreach events, and connected students with practicing engineers and alumni.",
  },
];

const capabilities = [
  "C/C++",
  "Java",
  "JavaScript/TypeScript",
  "Django",
  "Flask",
  ".NET",
  "SQL",
  "Pandas",
  "scikit-learn",
  "REST APIs",
];

const educationLogos: LogoItem[] = [
  {
    name: "Texas A&M University",
    src: "https://commons.wikimedia.org/wiki/Special:FilePath/Texas%20A%26M%20University%20logo.svg",
  },
  {
    name: "Texas Tech University",
    src: "https://commons.wikimedia.org/wiki/Special:FilePath/Texas%20Tech%20New%20Logo.svg",
  },
  {
    name: "TTU Health Sciences Center",
    src: "https://commons.wikimedia.org/wiki/Special:FilePath/Texas%20Tech%20University%20Health%20Sciences%20Center%20logo.svg",
  },
];

const techLogos: LogoItem[] = [
  { name: "Python", src: "https://cdn.simpleicons.org/python/3776AB" },
  { name: "React", src: "https://cdn.simpleicons.org/react/61DAFB" },
  { name: "Next.js", src: "https://cdn.simpleicons.org/nextdotjs/FFFFFF" },
  { name: "Node.js", src: "https://cdn.simpleicons.org/nodedotjs/5FA04E" },
  { name: "Docker", src: "https://cdn.simpleicons.org/docker/2496ED" },
  {
    name: "Azure",
    src: "https://cdn.simpleicons.org/microsoftazure/0078D4",
  },
  { name: "PyTorch", src: "https://cdn.simpleicons.org/pytorch/EE4C2C" },
  { name: "TensorFlow", src: "https://cdn.simpleicons.org/tensorflow/FF6F00" },
  { name: "MongoDB", src: "https://cdn.simpleicons.org/mongodb/47A248" },
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
    if (progress < 0.23) return "origin";
    if (progress < 0.48) return "work";
    if (progress < 0.72) return "craft";
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
            <a className="transition hover:text-white" href="#experience">
              Experience
            </a>
            <a className="transition hover:text-white" href="#skills">
              Skills
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
              MS Computer Science at Texas A&M
            </p>
            <h1 className="max-w-5xl text-5xl font-semibold leading-none text-white sm:text-7xl lg:text-8xl">
              Yeshas Krishna builds software that moves fast and teaches well.
            </h1>
            <p className="mt-7 max-w-2xl text-lg leading-8 text-white/74 sm:text-xl">
              Full-stack engineer, AI builder, and former teaching assistant
              focused on dependable products, adaptive learning tools, and
              systems that help real users do better work.
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
                href="mailto:krishnayeshas@gmail.com"
              >
                Contact me
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
              Texas A&M MS CS, GPA 4.00. Texas Tech CS, Summa Cum Laude, GPA
              3.91. Based in Texas.
            </p>
            <div className="mt-6 grid grid-cols-3 gap-3">
              {educationLogos.map((logo) => (
                <div
                  className="logo-cell flex min-h-20 items-center justify-center border border-white/12 bg-white/[0.07] p-3"
                  key={logo.name}
                >
                  <img
                    alt={`${logo.name} logo`}
                    className="max-h-11 max-w-full object-contain"
                    src={logo.src}
                  />
                </div>
              ))}
            </div>
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
              Projects with real-time collaboration, AI, and production impact.
            </h2>
          </div>

          <div className="mt-12 grid gap-4 md:grid-cols-3">
            {projects.map((project, index) => (
              <article
                className="project-tile min-h-[370px] border border-white/14 bg-white/[0.08] p-6 backdrop-blur-xl"
                key={project.title}
              >
                <div className="flex h-full flex-col justify-between">
                  <div>
                    <div className="mb-8 flex items-center justify-between gap-4 text-sm text-white/55">
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
                  <p className="mt-10 text-sm leading-6 text-white/55">
                    {project.stack}
                  </p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="experience" className="relative z-10 px-5 py-28 sm:py-36">
        <div className="mx-auto max-w-6xl">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase text-[#ff7a5c]">
              Experience
            </p>
            <h2 className="mt-4 text-4xl font-semibold leading-tight sm:text-6xl">
              Engineering, teaching, and leadership across technical teams.
            </h2>
          </div>

          <div className="mt-12 grid gap-4">
            {experiences.map((item) => (
              <article
                className="experience-row grid gap-6 border border-white/14 bg-black/28 p-6 backdrop-blur-xl lg:grid-cols-[260px_1fr]"
                key={`${item.role}-${item.organization}`}
              >
                <div>
                  <div className="logo-cell mb-5 flex h-20 w-24 items-center justify-center border border-white/12 bg-white/[0.07] p-3">
                    <img
                      alt={`${item.organization} logo`}
                      className="max-h-12 max-w-full object-contain"
                      src={item.logo}
                    />
                  </div>
                  <p className="text-sm font-semibold uppercase text-white/50">
                    {item.dates}
                  </p>
                  <p className="mt-3 text-sm text-white/55">{item.location}</p>
                </div>
                <div>
                  <h3 className="text-2xl font-semibold text-white">
                    {item.role}
                  </h3>
                  <p className="mt-2 text-base font-medium text-[#7fffd4]">
                    {item.organization}
                  </p>
                  <p className="mt-5 max-w-3xl text-base leading-7 text-white/68">
                    {item.impact}
                  </p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="skills" className="relative z-10 px-5 py-28 sm:py-36">
        <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
          <div className="sticky top-28">
            <p className="text-sm font-semibold uppercase text-[#ffd166]">
              Skills
            </p>
            <h2 className="mt-4 text-4xl font-semibold leading-tight sm:text-6xl">
              Full-stack foundations with an AI and data science edge.
            </h2>
            <div className="education-panel mt-8 border border-white/14 bg-white/[0.08] p-6 backdrop-blur-xl">
              <p className="text-sm font-semibold uppercase text-white/50">
                Education
              </p>
              <div className="mt-5 flex items-center gap-4">
                <img
                  alt="Texas A&M University logo"
                  className="h-12 w-16 object-contain"
                  src="https://commons.wikimedia.org/wiki/Special:FilePath/Texas%20A%26M%20University%20logo.svg"
                />
                <div>
                  <p className="text-xl font-semibold text-white">
                    Texas A&M University
                  </p>
                  <p className="mt-1 text-sm leading-6 text-white/62">
                    MS in Computer Science, expected Dec 2027. GPA 4.00.
                  </p>
                </div>
              </div>
              <div className="mt-6 flex items-center gap-4">
                <img
                  alt="Texas Tech University logo"
                  className="h-12 w-16 object-contain"
                  src="https://commons.wikimedia.org/wiki/Special:FilePath/Texas%20Tech%20New%20Logo.svg"
                />
                <div>
                  <p className="text-xl font-semibold text-white">
                    Texas Tech University Honors College
                  </p>
                  <p className="mt-1 text-sm leading-6 text-white/62">
                    BS in Computer Science, Summa Cum Laude. GPA 3.91.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div>
            <div className="logo-wall grid grid-cols-3 gap-4 sm:grid-cols-3">
              {techLogos.map((logo) => (
                <div
                  className="logo-cell flex min-h-28 flex-col items-center justify-center gap-3 border border-white/14 bg-black/28 p-4 backdrop-blur-xl"
                  key={logo.name}
                >
                  <img
                    alt={`${logo.name} logo`}
                    className="h-9 w-9 object-contain"
                    src={logo.src}
                  />
                  <span className="text-center text-sm font-semibold text-white/78">
                    {logo.name}
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              {capabilities.map((item) => (
                <div
                  className="skill-tile flex min-h-24 items-center border border-white/14 bg-black/28 px-5 text-lg font-semibold text-white backdrop-blur-xl"
                  key={item}
                >
                  {item}
                </div>
              ))}
            </div>
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
              Let us build something useful, polished, and fast.
            </h2>
            <div>
              <a
                className="inline-flex min-h-12 w-full items-center justify-center border border-white bg-white px-5 text-sm font-semibold text-black transition hover:bg-transparent hover:text-white"
                href="mailto:krishnayeshas@gmail.com"
              >
                krishnayeshas@gmail.com
              </a>
              <div className="mt-4 grid gap-3 text-sm text-white/65">
                <a
                  className="transition hover:text-white"
                  href="tel:+18064013151"
                >
                  +1 (806) 401-3151
                </a>
                <a
                  className="transition hover:text-white"
                  href="https://linkedin.com/in/yeshaskrishna"
                >
                  linkedin.com/in/yeshaskrishna
                </a>
                <a
                  className="transition hover:text-white"
                  href="https://github.com/yesh-krish"
                >
                  github.com/yesh-krish
                </a>
              </div>
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
