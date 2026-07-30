import Head from "next/head";
import { useState } from "react";

type StoryChapter = {
  title: string;
  text: string;
  illustration: string; // emoji-based illustration
};

type Story = {
  title: string;
  speakerName: string;
  genre: string;
  chapters: StoryChapter[];
};

const GENRES = [
  { id: "adventure", label: "🏴‍☠️ Adventure", desc: "Pirate ships, hidden treasures, daring escapes" },
  { id: "fairytale", label: "🧚 Fairytale", desc: "Magic forests, talking animals, happy endings" },
  { id: "space", label: "🚀 Space", desc: "Rocket ships, friendly aliens, distant planets" },
  { id: "ocean", label: "🌊 Ocean", desc: "Mermaids, submarines, underwater kingdoms" },
  { id: "silly", label: "🤪 Silly", desc: "Giggly monsters, backwards days, noodle storms" },
  { id: "cozy", label: "🛌 Cozy", desc: "Warm blankets, sleepy bears, gentle lullabies" },
];

const MOCK_STORIES: Record<string, StoryChapter[]> = {
  adventure: [
    { title: "The Map in the Attic", text: "Once upon a time, in a creaky old house much like this one, there lived a map that nobody had unfolded in a hundred years. It smelled of cinnamon and faraway oceans. One rainy Tuesday, a tiny hand reached up and pulled it down...", illustration: "🗺️✨🏚️" },
    { title: "The Secret Passage", text: "The map whispered of a hidden door behind the grandfather clock. With a gentle push, the clock swung open to reveal a staircase lit by glowworms. 'Shall we?' whispered Grandma's voice.", illustration: "🕰️🚪✨" },
    { title: "The Treasure of True Stories", text: "At the bottom of the staircase was not gold or jewels, but a library of floating books — each one a story someone had truly lived. The most beautiful one glowed and fluttered toward you. It was labeled with your name.", illustration: "📚💫❤️" },
    { title: "Home, with a Secret", text: "You returned through the clock door just as the sun peeked through the curtains. The map tucked itself back into the attic. But every night since, a new page of your story writes itself — and Grandma reads it aloud.", illustration: "🏠🌅💤" },
  ],
  fairytale: [
    { title: "The Whispering Woods", text: "Beyond the garden gate, where the grass grows tall and the brambles tangle, there lies a wood that only wakes when children dream. Tonight, it stirred. A little fox with silver whiskers beckoned from the treeline...", illustration: "🌲🦊🌙" },
    { title: "The Kind Dragon", text: "Deep in the woods lived a dragon named Puffington who breathed not fire, but lavender-scented bubbles. He was terribly lonely, for everyone expected dragons to be fierce. But tonight, he had visitors.", illustration: "🐉🫧💜" },
    { title: "The Bridge of Wishes", text: "Puffington led the way to a bridge made entirely of dandelion fluff. 'Make a wish,' said Grandma's voice, 'but not for things. Wish for feelings — the best kind.' One by one, wishes floated up like little lanterns.", illustration: "🌉🌼✨" },
    { title: "The Promise", text: "As the last wish lantern disappeared into the stars, Puffington curled his tail around the group and hummed a song older than the woods themselves. 'You may return,' he rumbled, 'whenever you need a story.'", illustration: "🌟🐉💤" },
  ],
  space: [
    { title: "Blast Off at Bedtime", text: "The bedroom ceiling shimmered and dissolved into a thousand stars. The bed lifted gently, blankets and all, and drifted through the open window into the night sky. Destination: the Cheese Moon.", illustration: "🚀🌙🧀" },
    { title: "The Wobble Comet", text: "A wobbly little comet named Ziggy couldn't fly straight. All the other comets zoomed in perfect lines, but Ziggy zigzagged and loop-de-looped. 'That looks more fun anyway,' chuckled Grandma's voice.", illustration: "☄️💫😄" },
    { title: "Tea with Saturn", text: "Saturn invited everyone for tea on her rings. The cups floated. The teapot orbited around the table. Saturn told jokes so old that even the stars had forgotten them. Everyone laughed until their tummies hurt.", illustration: "🪐☕😆" },
    { title: "The Gentle Return", text: "As the bed drifted home, Ziggy the comet traced 'SWEET DREAMS' in stardust across the sky. The bedroom ceiling returned, but now it had tiny glow-in-the-dark stars that weren't there before.", illustration: "💫🌠😴" },
  ],
  ocean: [
    { title: "The Shell That Sang", text: "Down at the beach, under the light of a jellyfish moon, a shell the color of sunrise washed ashore. When held to an ear, it didn't just roar — it sang. A lullaby from the bottom of the sea.", illustration: "🐚🌊🎵" },
    { title: "Sebastian's Taxi", text: "A giant, friendly sea turtle named Sebastian offered his shell as a submarine taxi. 'Hop on,' he gurgled. 'Tonight's tour includes the Coral Concert and the Kelp Forest Ballet.'", illustration: "🐢🚕🪸" },
    { title: "The Glowing Garden", text: "The Coral Concert was in full swing — clownfish on trumpet, anglerfish on spotlight, octopus on eight different drums. The music made the anemones sway and the bioluminescent plankton dance in rainbow patterns.", illustration: "🐠🎺🪸" },
    { title: "Sunrise on the Shore", text: "Sebastian delivered everyone back to the beach just as the sun painted the sky pink. 'Same time tomorrow?' he asked, already swimming backward toward the deep. The singing shell hummed softly in a pocket.", illustration: "🌅🐢💤" },
  ],
  silly: [
    { title: "The Day Pancakes Took Over", text: "It started, as most silly things do, on a Tuesday. The pancakes on the griddle suddenly sprouted tiny legs and marched off the plate. 'Freedom!' squeaked the littlest one. They formed a pancake parliament in the living room.", illustration: "🥞🦵😂" },
    { title: "Professor Wobblebottom", text: "The pancakes elected Professor Wobblebottom, a particularly fluffy specimen with a blueberry monocle, as their leader. His first decree: 'All socks shall be worn on hands from now on.' Chaos, but the fun kind.", illustration: "🫐🎩🤣" },
    { title: "The Noodle Storm", text: "Suddenly — because in this story, things happen suddenly — a noodle storm rolled in. Spaghetti lightning! Ravioli hail! The pancakes deployed tiny umbrellas. A meatball rainbow arched across the kitchen sky.", illustration: "🍝⛈️🌈" },
    { title: "Bedtime, Really This Time", text: "The pancakes, exhausted from governing, marched back to the plate and tucked themselves under a napkin blanket. Professor Wobblebottom yawned. 'Same time next Tuesday?' And just like that, the house was quiet again.", illustration: "😴🥞💤" },
  ],
  cozy: [
    { title: "The Sleepy Bear's Secret", text: "In a cottage at the edge of a honey-colored meadow, lived a bear named Barnaby who was very, very good at one thing: being cozy. He knew the exact temperature for cocoa, the fluffiest pillow arrangement, and seven different ways to tuck someone in.", illustration: "🐻🍯🛏️" },
    { title: "The Cocoa Ceremony", text: "Barnaby believed that cocoa was not a drink but a ritual. He warmed the milk slowly, stirred exactly three times clockwise, and added one marshmallow for each bedtime story you'd ever loved. Tonight, the mug was very full.", illustration: "☕🤎🧸" },
    { title: "The Lullaby Library", text: "After cocoa, Barnaby led the way to a room full of hammocks and soft-glowing lanterns. Each hammock had a book already open to the right page. 'Pick any one,' he rumbled. 'They all end with stars.'", illustration: "📖🌟🎵" },
    { title: "Tucked In", text: "The story ended, as all the best do, with heavy eyelids and a contented sigh. Barnaby pulled the blanket to chin-height and hummed three low notes. Outside the window, a real bear — maybe, probably — waved goodnight.", illustration: "🛌🌙💤" },
  ],
};

function getStory(genre: string): StoryChapter[] {
  return MOCK_STORIES[genre] || MOCK_STORIES.adventure;
}

export default function Home() {
  const [step, setStep] = useState<"hero" | "record" | "genre" | "story">("hero");
  const [speakerName, setSpeakerName] = useState("");
  const [childName, setChildName] = useState("");
  const [selectedGenre, setSelectedGenre] = useState("");
  const [story, setStory] = useState<Story | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [hasRecording, setHasRecording] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleRecord = () => {
    setIsRecording(true);
    setHasRecording(false);
    // Mock recording: 3 seconds
    setTimeout(() => {
      setIsRecording(false);
      setHasRecording(true);
    }, 3000);
  };

  const handleGenerateStory = () => {
    setLoading(true);
    setTimeout(() => {
      const chapters = getStory(selectedGenre);
      setStory({
        title: `${childName || "Little One"}'s ${GENRES.find(g => g.id === selectedGenre)?.label.split(" ")[1] || ""} Adventure`,
        speakerName: speakerName || "Grandma",
        genre: selectedGenre,
        chapters,
      });
      setLoading(false);
      setStep("story");
    }, 1500);
  };

  const reset = () => {
    setStep("hero");
    setSpeakerName("");
    setChildName("");
    setSelectedGenre("");
    setStory(null);
    setHasRecording(false);
  };

  return (
    <>
      <Head>
        <title>Grandma&apos;s Voice — Bedtime Stories in Their Voice</title>
      </Head>

      <div className="min-h-screen bg-base-100" data-theme="retro">
        {/* Hero */}
        {step === "hero" && (
          <div className="hero min-h-screen bg-gradient-to-b from-amber-50 to-orange-100">
            <div className="hero-content text-center max-w-lg">
              <div className="space-y-6">
                <div className="text-7xl">👵🎙️✨</div>
                <h1 className="text-5xl font-bold text-walnut-800">
                  Grandma&apos;s Voice
                </h1>
                <p className="text-xl text-stone-600 leading-relaxed">
                  Record a loved one&apos;s voice and generate a magical bedtime story
                  <br />
                  <span className="font-semibold text-amber-700">narrated by them</span> — for the little ones who miss them most.
                </p>
                <div className="flex flex-col sm:flex-row gap-3 justify-center pt-4">
                  <button
                    onClick={() => setStep("record")}
                    className="btn btn-primary btn-lg gap-2"
                  >
                    🎙️ Start Recording
                  </button>
                  <button
                    onClick={() => {
                      setHasRecording(true);
                      setStep("genre");
                    }}
                    className="btn btn-outline btn-lg gap-2"
                  >
                    ⏭️ Skip to Story
                  </button>
                </div>
                <p className="text-sm text-stone-400 italic pt-2">
                  &ldquo;I made a story with Grandma&apos;s voice.&rdquo; — every forwarded message ever.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Record */}
        {step === "record" && (
          <div className="hero min-h-screen bg-gradient-to-b from-rose-50 to-amber-50">
            <div className="hero-content text-center max-w-lg">
              <div className="space-y-6 w-full">
                <h2 className="text-3xl font-bold text-stone-800">Step 1: Capture Their Voice</h2>
                <p className="text-stone-500">
                  Just 30 seconds — read a short passage, tell a joke, or say &ldquo;I love you.&rdquo;
                </p>

                <div className="form-control w-full max-w-xs mx-auto">
                  <label className="label">
                    <span className="label-text font-medium">Who&apos;s speaking?</span>
                  </label>
                  <input
                    type="text"
                    placeholder="Grandma, Grandpa, Auntie..."
                    className="input input-bordered w-full"
                    value={speakerName}
                    onChange={(e) => setSpeakerName(e.target.value)}
                  />
                </div>

                <div className="form-control w-full max-w-xs mx-auto">
                  <label className="label">
                    <span className="label-text font-medium">Who&apos;s the story for?</span>
                  </label>
                  <input
                    type="text"
                    placeholder="Child's name"
                    className="input input-bordered w-full"
                    value={childName}
                    onChange={(e) => setChildName(e.target.value)}
                  />
                </div>

                <div className="flex flex-col items-center gap-4 pt-4">
                  {!hasRecording ? (
                    <>
                      <button
                        onClick={handleRecord}
                        disabled={isRecording}
                        className={`btn btn-circle btn-lg ${
                          isRecording ? "btn-error animate-pulse" : "btn-primary"
                        }`}
                      >
                        {isRecording ? "⏺️" : "🎙️"}
                      </button>
                      <p className="text-sm text-stone-500">
                        {isRecording ? "Recording... speak now!" : "Tap to record 30 seconds"}
                      </p>
                      {isRecording && (
                        <div className="flex gap-1 items-center">
                          {[1, 2, 3, 4, 5].map((i) => (
                            <div
                              key={i}
                              className="w-2 bg-primary rounded-full animate-bounce"
                              style={{
                                height: `${10 + Math.random() * 30}px`,
                                animationDelay: `${i * 0.1}s`,
                              }}
                            />
                          ))}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="space-y-4 text-center">
                      <div className="text-6xl">✅</div>
                      <p className="text-lg font-semibold text-green-700">
                        Voice captured!
                      </p>
                      <p className="text-stone-500 text-sm">
                        {speakerName || "Grandma"}&apos;s voice is ready. Let&apos;s pick a story.
                      </p>
                    </div>
                  )}
                </div>

                <div className="flex gap-3 justify-center pt-4">
                  <button onClick={() => setStep("hero")} className="btn btn-ghost">
                    ← Back
                  </button>
                  <button
                    onClick={() => setStep("genre")}
                    className="btn btn-primary"
                    disabled={!hasRecording}
                  >
                    Pick a Story →
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Genre Picker */}
        {step === "genre" && (
          <div className="hero min-h-screen bg-gradient-to-b from-purple-50 to-pink-50">
            <div className="hero-content text-center max-w-2xl">
              <div className="space-y-6 w-full">
                <h2 className="text-3xl font-bold text-stone-800">Step 2: Pick Tonight&apos;s Adventure</h2>
                <p className="text-stone-500">
                  What kind of story would {childName || "they"} love tonight?
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {GENRES.map((genre) => (
                    <button
                      key={genre.id}
                      onClick={() => setSelectedGenre(genre.id)}
                      className={`btn btn-lg h-auto py-4 flex flex-col items-start gap-1 ${
                        selectedGenre === genre.id
                          ? "btn-primary"
                          : "btn-outline"
                      }`}
                    >
                      <span className="text-2xl">{genre.label}</span>
                      <span className="text-xs font-normal opacity-70 text-left">
                        {genre.desc}
                      </span>
                    </button>
                  ))}
                </div>

                <div className="flex gap-3 justify-center pt-4">
                  <button onClick={() => setStep("record")} className="btn btn-ghost">
                    ← Back
                  </button>
                  <button
                    onClick={handleGenerateStory}
                    className="btn btn-primary btn-lg gap-2"
                    disabled={!selectedGenre || loading}
                  >
                    {loading ? (
                      <>
                        <span className="loading loading-spinner"></span>
                        Weaving magic...
                      </>
                    ) : (
                      "✨ Generate Story"
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Story View */}
        {step === "story" && story && (
          <div className="min-h-screen bg-gradient-to-b from-amber-50 via-orange-50 to-rose-50">
            <div className="max-w-2xl mx-auto px-4 py-8 space-y-8">
              {/* Story header */}
              <div className="text-center space-y-3 pt-4">
                <p className="text-sm uppercase tracking-widest text-stone-400">
                  A Bedtime Story Narrated By
                </p>
                <div className="flex items-center justify-center gap-3">
                  <span className="text-4xl">👵</span>
                  <h1 className="text-2xl sm:text-3xl font-bold text-stone-800">
                    {speakerName || "Grandma"}
                  </h1>
                </div>
                <p className="text-stone-500 italic">
                  for {childName || "their favorite little one"}
                </p>
                <div className="badge badge-lg badge-outline gap-1">
                  {GENRES.find(g => g.id === selectedGenre)?.label}
                </div>
              </div>

              {/* Chapters */}
              <div className="space-y-6">
                {story.chapters.map((chapter, i) => (
                  <div key={i} className="card bg-white/80 backdrop-blur shadow-lg border border-amber-100 overflow-hidden">
                    <div className="card-body p-6">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="badge badge-primary badge-sm">Chapter {i + 1}</span>
                      </div>
                      <div className="text-center text-5xl mb-3">
                        {chapter.illustration}
                      </div>
                      <h2 className="card-title text-xl text-stone-700 justify-center text-center">
                        {chapter.title}
                      </h2>
                      <p className="text-stone-600 leading-relaxed text-lg text-center">
                        &ldquo;{chapter.text}&rdquo;
                      </p>
                      <p className="text-xs text-right text-stone-400 italic mt-2">
                        — read in {speakerName || "Grandma"}&apos;s voice 🎙️
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center pb-12">
                <button
                  onClick={() => {
                    setStep("genre");
                    setSelectedGenre("");
                    setStory(null);
                  }}
                  className="btn btn-outline gap-2"
                >
                  📖 Pick Another Story
                </button>
                <button
                  onClick={() => {
                    const text = story.chapters.map((c, i) => `Chapter ${i + 1}: ${c.title}\n${c.text}\n`).join("\n");
                    navigator.clipboard.writeText(text);
                  }}
                  className="btn btn-primary gap-2"
                >
                  📋 Copy Story
                </button>
                <button onClick={reset} className="btn btn-ghost gap-2">
                  🏠 Start Over
                </button>
              </div>

              {/* Share prompt */}
              <div className="text-center pb-8">
                <div className="alert bg-amber-100 border border-amber-200 max-w-md mx-auto">
                  <span>💡</span>
                  <span className="text-sm text-amber-800">
                    Forward this to the family group chat. Trust us — it&apos;ll make someone&apos;s night.
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