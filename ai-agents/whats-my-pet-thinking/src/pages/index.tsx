import Head from "next/head";
import { useState } from "react";

type PetType = "dog" | "cat" | "bird" | "hamster" | "rabbit" | "other";

type Monologue = {
  text: string;
  emoji: string;
  title: string;
};

const PET_EMOJIS: Record<PetType, string> = {
  dog: "🐕",
  cat: "🐈",
  bird: "🐦",
  hamster: "🐹",
  rabbit: "🐰",
  other: "🐾",
};

const PET_TYPES: { value: PetType; label: string }[] = [
  { value: "dog", label: "🐕 Dog" },
  { value: "cat", label: "🐈 Cat" },
  { value: "bird", label: "🐦 Bird" },
  { value: "hamster", label: "🐹 Hamster" },
  { value: "rabbit", label: "🐰 Rabbit" },
  { value: "other", label: "🐾 Other" },
];

// Mock monologue generator — keyword-based matching for fun variety
function generateMonologue(
  petName: string,
  petType: PetType,
  behavior: string
): Monologue {
  const lower = behavior.toLowerCase();

  // Dog monologues
  if (petType === "dog") {
    if (lower.includes("staring") || lower.includes("nothing") || lower.includes("wall")) {
      return {
        emoji: "🐕",
        title: "The Vigilant Protector",
        text: `I sense... a disturbance in the snack force. Someone within a 3-block radius just opened a cheese wrapper. ${petName} is ON IT. Also, that wall just looked at me funny. Don't worry, I stared back until it behaved. You're welcome.`,
      };
    }
    if (lower.includes("zoom") || lower.includes("running") || lower.includes("crazy") || lower.includes("sprint")) {
      return {
        emoji: "🐕",
        title: "Zoomies: An Autobiography",
        text: `I HAVE NO IDEA WHY I'M RUNNING BUT I HAVE TO RUN. THE FLOOR IS ELECTRIC. MY LEGS ARE POSSESSED. ${petName.toUpperCase()} MODE: ACTIVATED. Couch → hallway → kitchen → couch → REPEAT. Physics? Never heard of her. I'll crash in 90 seconds and sleep for 3 hours.`,
      };
    }
    if (lower.includes("tail") || lower.includes("chase")) {
      return {
        emoji: "🐕",
        title: "The Eternal Pursuit",
        text: `It's back there again. Following me. Everywhere I turn, it's RIGHT THERE. I've been chasing this thing for 2 years and I WILL catch it. Mark my words, human. Today is the day. ${petName} doesn't give up. I just need... one more... spin...`,
      };
    }
    if (lower.includes("guilty") || lower.includes("shoe") || lower.includes("chew") || lower.includes("destroy")) {
      return {
        emoji: "🐕",
        title: "The Defense Rests",
        text: `Look, I can explain. The shoe... it attacked first. It was just sitting there, MENACINGLY. I had no choice but to defend this household. ${petName} is a hero, not a criminal. That guilty face? I'm just tired from all the heroism. Also, I regret nothing.`,
      };
    }
    if (lower.includes("bath") || lower.includes("wet") || lower.includes("water")) {
      return {
        emoji: "🐕",
        title: "The Great Betrayal",
        text: `I trusted you. I TRUSTED YOU. And you brought me to the Wet Place. The floor is now a lake. I smell like... flowers? This is an outrage. ${petName} will remember this. The post-bath zoomies are coming, and they will be LEGENDARY.`,
      };
    }
    return {
      emoji: "🐕",
      title: "A Dog's Life",
      text: `Today's agenda: woke up, stretched dramatically (nailed it), ate breakfast in 4.3 seconds, napped from 9:07 to 11:42, barked at the mailman (he knows what he did), napped again, and now I'm here with you. ${petName}'s life is EXHAUSTING but someone has to do it.`,
    };
  }

  // Cat monologues
  if (petType === "cat") {
    if (lower.includes("knock") || lower.includes("push") || lower.includes("table") || lower.includes("shelf")) {
      return {
        emoji: "🐈",
        title: "Gravity Research Division",
        text: `Gravity check complete. This mug is functional. That vase? Also functional. I'm basically a scientist. ${petName}, PhD in Applied Physics. My research confirms: everything falls. Every. Single. Time. The humans call it "destruction." I call it peer-reviewed methodology.`,
      };
    }
    if (lower.includes("3am") || lower.includes("night") || lower.includes("midnight") || lower.includes("sleep")) {
      return {
        emoji: "🐈",
        title: "The 3 AM Sermon",
        text: `IT IS 3:00 AM AND THE FOOD BOWL IS VISIBLE. Not empty. Visible. There's a difference. ${petName} must sing the song of our people until this injustice is corrected. MROOOOOW. Also, I just remembered I can see the bottom of the bowl. MROOOOOOOWWWWW.`,
      };
    }
    if (lower.includes("box") || lower.includes("sit") || lower.includes("cardboard")) {
      return {
        emoji: "🐈",
        title: "If I Fits, I Sits",
        text: `This box is 3 sizes too small. Perfect. ${petName} has claimed this territory in the name of Cat Kingdom. The $80 bed you bought? Offensive. This cardboard from Amazon? A throne. I don't make the rules. Actually, I do. I make all the rules.`,
      };
    }
    if (lower.includes("laser") || lower.includes("red dot")) {
      return {
        emoji: "🐈",
        title: "The Uncatchable One",
        text: `It's back. The red dot. The eternal nemesis of ${petName}. I've trained for this my entire life. 14 hours of napping prepared me for this moment. Today... TODAY I will catch it. Wait, where'd it go? IT'S ON THE CEILING. This is an unfair arena.`,
      };
    }
    return {
      emoji: "🐈",
      title: "Judgment Day",
      text: `You're 3 minutes late with dinner. ${petName} noticed. ${petName} always notices. I'm not angry, just... disappointed. Actually, no, I'm both. But I'll forgive you because you're warm and you have thumbs. Now, the food. We're at DEFCON 2.`,
    };
  }

  // Bird monologues
  if (petType === "bird") {
    if (lower.includes("mirror") || lower.includes("reflection")) {
      return {
        emoji: "🐦",
        title: "The Rival",
        text: `There's another bird in the shiny thing. ${petName} has been negotiating with him for 45 minutes. He's very stubborn. He repeats everything I say. But I WILL win this debate. He blinked first. Wait, no, I blinked. Okay, rematch.`,
      };
    }
    return {
      emoji: "🐦",
      title: "The Morning Announcement",
      text: `GOOD MORNING EVERYONE. ${petName} here with the 6:00 AM news. The sun is up! The sun is up! The sun is up! This concludes the news. I will now repeat this bulletin every 30 seconds until you acknowledge my journalistic excellence. SQUAWK.`,
    };
  }

  // Hamster monologues
  if (petType === "hamster") {
    if (lower.includes("wheel") || lower.includes("running")) {
      return {
        emoji: "🐹",
        title: "The Marathon",
        text: `I've been running for 3 hours. Distance covered: zero miles. Destination: nowhere. ${petName}'s fitness tracker is VERY confused. But I don't care — I'm training for the Hamster Olympics. Gold medal in Circular Sprinting. I'm a legend in my own wheel.`,
      };
    }
    return {
      emoji: "🐹",
      title: "Operation Cheek Pouch",
      text: `You gave me one sunflower seed. ONE. ${petName} is insulted. I've stuffed both cheeks with enough bedding to build a second house. You think I'm cute? I'm a logistics mastermind. These cheeks aren't just adorable — they're strategic reserves.`,
    };
  }

  // Rabbit monologues
  if (petType === "rabbit") {
    return {
      emoji: "🐰",
      title: "The Binky Report",
      text: `I just did a binky. That's a mid-air twist for you non-rabbits. ${petName} is feeling JOYFUL. The hay is fresh, the sun is warm, and I haven't been betrayed by a cucumber today. Life is good. I might do another binky. I DID IT.`,
    };
  }

  // Generic / other
  if (lower.includes("hungry") || lower.includes("food") || lower.includes("eat")) {
    return {
      emoji: PET_EMOJIS[petType],
      title: "The Hunger Games",
      text: `The food bowl is at 47% capacity. This is an EMERGENCY. ${petName} is wasting away. I haven't eaten in... what even is time? At least 20 minutes? I'm basically a survivor. A warrior. A very hungry, very dramatic warrior.`,
    };
  }

  return {
    emoji: PET_EMOJIS[petType],
    title: "Inner Thoughts",
    text: `You're looking at me like I'm doing something weird. ${petName} would like to remind you that YOU'RE the weird one. You don't have fur. You walk on two legs. You pay money for lettuce. I'm not judging you. Okay, I'm absolutely judging you. But I love you anyway.`,
  };
}

export default function Home() {
  const [step, setStep] = useState<"hero" | "input" | "loading" | "result">("hero");
  const [petName, setPetName] = useState("");
  const [petType, setPetType] = useState<PetType>("dog");
  const [behavior, setBehavior] = useState("");
  const [monologue, setMonologue] = useState<Monologue | null>(null);
  const [copied, setCopied] = useState(false);

  const handleGenerate = () => {
    setStep("loading");
    // Simulate LLM thinking time
    setTimeout(() => {
      const result = generateMonologue(petName || "My pet", petType, behavior);
      setMonologue(result);
      setStep("result");
    }, 1800);
  };

  const handleCopy = () => {
    if (!monologue) return;
    const text = `🐾 What's ${petName || "My Pet"} Thinking?\n\n"${monologue.text}"\n\n— ${petName || "My pet"}, ${new Date().toLocaleDateString()}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const reset = () => {
    setStep("hero");
    setPetName("");
    setPetType("dog");
    setBehavior("");
    setMonologue(null);
    setCopied(false);
  };

  const goAgain = () => {
    setStep("input");
    setBehavior("");
    setMonologue(null);
    setCopied(false);
  };

  return (
    <>
      <Head>
        <title>What&apos;s My Pet Thinking? — Hilarious Pet Inner Monologues</title>
      </Head>

      <div data-theme="cupcake" className="min-h-screen">
        {/* Hero */}
        {step === "hero" && (
          <div className="hero min-h-screen bg-gradient-to-b from-pink-100 via-purple-50 to-blue-50">
            <div className="hero-content text-center max-w-lg">
              <div className="space-y-6">
                <div className="text-7xl">🐕🐈🐹🐰🐦</div>
                <h1 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-500">
                  What&apos;s My Pet Thinking?
                </h1>
                <p className="text-xl text-stone-600 leading-relaxed">
                  Describe your pet doing something weird, and we&apos;ll reveal
                  <br />
                  <span className="font-bold text-purple-600">their honest inner monologue</span>
                  {" "}— the one they&apos;d never admit to.
                </p>
                <div className="pt-4">
                  <button
                    onClick={() => setStep("input")}
                    className="btn btn-primary btn-lg gap-2 text-lg"
                  >
                    🐾 Reveal Their Thoughts
                  </button>
                </div>
                <div className="flex flex-wrap justify-center gap-4 pt-4 text-stone-400">
                  <div className="flex items-center gap-1">
                    <span className="text-lg">🐕</span>
                    <span className="text-sm">&ldquo;The wall looked at me funny&rdquo;</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-lg">🐈</span>
                    <span className="text-sm">&ldquo;Gravity test complete&rdquo;</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-lg">🐹</span>
                    <span className="text-sm">&ldquo;Marathon to nowhere&rdquo;</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Input */}
        {step === "input" && (
          <div className="hero min-h-screen bg-gradient-to-b from-purple-50 to-pink-50">
            <div className="hero-content text-center max-w-lg w-full">
              <div className="space-y-6 w-full">
                <h2 className="text-3xl font-bold text-stone-800">
                  Tell Me About Your Pet
                </h2>
                <p className="text-stone-500">
                  What weird thing are they doing right now?
                </p>

                <div className="form-control w-full">
                  <label className="label">
                    <span className="label-text font-semibold">Pet&apos;s Name</span>
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Luna, Max, Sir Whiskers III"
                    className="input input-bordered w-full text-lg"
                    value={petName}
                    onChange={(e) => setPetName(e.target.value)}
                  />
                </div>

                <div className="form-control w-full">
                  <label className="label">
                    <span className="label-text font-semibold">Pet Type</span>
                  </label>
                  <select
                    className="select select-bordered w-full text-lg"
                    value={petType}
                    onChange={(e) => setPetType(e.target.value as PetType)}
                  >
                    {PET_TYPES.map((pt) => (
                      <option key={pt.value} value={pt.value}>
                        {pt.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-control w-full">
                  <label className="label">
                    <span className="label-text font-semibold">What are they doing?</span>
                  </label>
                  <textarea
                    className="textarea textarea-bordered w-full text-lg h-28"
                    placeholder="e.g. Staring at the wall for 10 minutes straight... or knocking everything off the coffee table one by one..."
                    value={behavior}
                    onChange={(e) => setBehavior(e.target.value)}
                  />
                </div>

                <div className="flex gap-3 justify-center pt-2">
                  <button
                    onClick={() => setStep("hero")}
                    className="btn btn-ghost"
                  >
                    ← Back
                  </button>
                  <button
                    onClick={handleGenerate}
                    className="btn btn-primary btn-lg gap-2"
                    disabled={!behavior.trim()}
                  >
                    🔮 Reveal Their Thoughts
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Loading */}
        {step === "loading" && (
          <div className="hero min-h-screen bg-gradient-to-b from-purple-50 to-pink-50">
            <div className="hero-content text-center max-w-lg">
              <div className="space-y-8">
                <div className="text-6xl animate-bounce">
                  {PET_EMOJIS[petType]}
                </div>
                <h2 className="text-2xl font-bold text-stone-700">
                  Tuning into {petName || "your pet"}&apos;s brainwaves...
                </h2>
                <div className="flex justify-center gap-2">
                  <span className="loading loading-dots loading-lg text-primary"></span>
                </div>
                <div className="space-y-2 text-stone-400 text-sm italic">
                  <p className="animate-pulse">🐾 Decoding tail language...</p>
                  <p className="animate-pulse" style={{ animationDelay: "0.5s" }}>
                    🧠 Translating from Pet to Human...
                  </p>
                  <p className="animate-pulse" style={{ animationDelay: "1s" }}>
                    ✨ Adding dramatic flair...
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Result */}
        {step === "result" && monologue && (
          <div className="min-h-screen bg-gradient-to-b from-purple-50 via-pink-50 to-amber-50">
            <div className="max-w-2xl mx-auto px-4 py-8 space-y-8">
              {/* Header */}
              <div className="text-center pt-6 space-y-3">
                <p className="text-sm uppercase tracking-widest text-stone-400">
                  The Inner Monologue of
                </p>
                <div className="text-7xl">{monologue.emoji}</div>
                <h1 className="text-3xl font-extrabold text-stone-800">
                  {petName || "Your Pet"}
                </h1>
                <div className="badge badge-lg badge-primary gap-1">
                  {PET_TYPES.find((p) => p.value === petType)?.label}
                </div>
              </div>

              {/* Monologue card */}
              <div className="card bg-white/90 backdrop-blur shadow-xl border-2 border-purple-200 overflow-hidden">
                <div className="card-body p-8">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="badge badge-secondary badge-sm gap-1">
                      💭 {monologue.title}
                    </span>
                  </div>
                  <div className="text-5xl text-center mb-4">
                    {monologue.emoji}
                  </div>
                  <blockquote className="text-lg leading-relaxed text-stone-700 italic text-center border-l-4 border-purple-400 pl-4 py-2">
                    &ldquo;{monologue.text}&rdquo;
                  </blockquote>
                  <p className="text-right text-xs text-stone-400 mt-4">
                    — {petName || "Your pet"}, as translated by AI 🐾
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center pb-4">
                <button
                  onClick={handleCopy}
                  className={`btn gap-2 ${copied ? "btn-success" : "btn-primary"}`}
                >
                  {copied ? "✅ Copied!" : "📋 Copy to Clipboard"}
                </button>
                <button onClick={goAgain} className="btn btn-outline btn-secondary gap-2">
                  🔄 Generate Another
                </button>
                <button onClick={reset} className="btn btn-ghost gap-2">
                  🏠 Start Over
                </button>
              </div>

              {/* Share prompt */}
              <div className="text-center pb-8">
                <div className="alert bg-purple-100 border border-purple-200 max-w-md mx-auto">
                  <span>📸</span>
                  <span className="text-sm text-purple-800">
                    Screenshot this and share it in the group chat. Pet content is the most shared thing on the internet — make your pet famous.
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}