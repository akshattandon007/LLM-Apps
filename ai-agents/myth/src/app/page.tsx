'use client';

import { useState } from 'react';

// ── Mock data for generating varied Wikipedia-style articles ──

const ERA_DATA: Record<string, {
  prefix: string; nation: string; occupations: string[];
  earlyLifeTemplates: string[]; careerTemplates: string[];
  controversyTemplates: string[]; legacyTemplates: string[];
  seeAlso: string[];
}> = {
  'Victorian inventor': {
    prefix: 'Sir',
    nation: 'British',
    occupations: ['Inventor', 'Engineer', 'Eccentric', 'Gentleman Scholar'],
    earlyLifeTemplates: [
      'Born to a family of modest means in rural England, {name} showed an early fascination with mechanical contraptions, reportedly building a working steam-powered butter churn by age 12.',
      'The child of a clockmaker and a poet, {name} spent their formative years disassembling household appliances and alarming the neighbours with small explosions.',
      'Orphaned at a young age and raised by a reclusive aunt who collected taxidermied squirrels, {name} found solace in the workshop of a local blacksmith.',
    ],
    careerTemplates: [
      'In {year}, {name} unveiled their most famous creation: the {invention}, a device that promised to revolutionise {field}. The Royal Society was, by most accounts, deeply confused.',
      '{name}\'s breakthrough came during a particularly dull Tuesday when they accidentally discovered the principles of {discovery}. The scientific community promptly ignored it for 40 years.',
      'After a series of failed experiments involving mercury, copper wire, and an uncooperative badger, {name} stumbled upon what they called "the principle of {principle}," which would later be proven entirely wrong but charming nonetheless.',
    ],
    controversyTemplates: [
      'In {year2}, {name} was accused of stealing credit from their assistant, a former chimney sweep named Bartholomew, who had actually done most of the inventing while {name} was at the pub.',
      'The publication of "{name}\'s Treatise on {topic}" caused a minor scandal when it was discovered that three of the four diagrams had been copied from a tea towel.',
      'Rival inventor Lord Pemberton publicly challenged {name} to a duel of wits at the Royal Academy. {name} won by simply talking about gears for four hours until Pemberton fell asleep.',
    ],
    legacyTemplates: [
      'While largely forgotten today, {name}\'s work laid the groundwork for modern {modernField}. A small plaque exists somewhere in Birmingham, though nobody has found it since 1987.',
      '{name} died in {deathYear}, reportedly while attempting to build a flying bicycle. Their last words were said to be "it works in theory."',
      'The {name} Society, founded in 1923 by three enthusiasts who had read about {name} in a pamphlet, still meets annually in a pub near Manchester.',
    ],
    seeAlso: [
      'List of inventors who died trying to prove a point',
      'The Great Steam-Powered Pigeon Incident of 1887',
      'Eccentricity in Victorian England',
      'Things that probably shouldn\'t have been electrified',
    ],
  },
  'Renaissance artist': {
    prefix: 'Maestro',
    nation: 'Italian',
    occupations: ['Painter', 'Sculptor', 'Anatomy Enthusiast', 'Professional Rival'],
    earlyLifeTemplates: [
      'Born in a small Tuscan village to a cheese merchant and a woman of "mysterious origin," {name} first demonstrated artistic talent by sketching remarkably accurate portraits of the family goat.',
      'Apprenticed at age 9 to a master fresco painter who was going blind, {name} learned that great art is 90% confidence and 10% not falling off the scaffolding.',
      'Legend holds that the young {name} could draw a perfect circle freehand. Less legendarily, they also drew perfect caricatures of the local bishop that got them briefly excommunicated.',
    ],
    careerTemplates: [
      'Commissioned by the powerful Medici family to paint "The {scene}," {name} delivered a work so stunning that the Medicis immediately locked it in a private chamber for 200 years so nobody else could see it.',
      '{name}\'s rival, the painter Giovanni di Mediocre, publicly claimed {name} couldn\'t paint hands. {name} responded by painting an entire fresco of nothing but hands — 147 of them — each one perfect.',
      'In {year}, {name} unveiled a sculpture that was so lifelike, local authorities briefly arrested it for loitering.',
    ],
    controversyTemplates: [
      'Art historians still debate whether {name} really painted the mysterious "Portrait of a Smirking Nobleman" or whether, as one theory suggests, it was painted by a particularly talented horse.',
      'The Church investigated {name} after the unveiling of "{artwork}" which contained what appeared to be a hidden portrait of the Pope\'s dog in an undignified position.',
      '{name} was briefly imprisoned for "excessive use of the colour ultramarine," which at the time was more expensive than gold and technically belonged to the Duke.',
    ],
    legacyTemplates: [
      '{name}\'s work influenced generations of artists, particularly in the technique of {technique}, which remains taught in art schools despite no one fully understanding it.',
      'In {deathYear}, {name} passed away under mysterious circumstances involving a rival, a bowl of poisoned olives, and a very smug cat that seemed to know more than it was letting on.',
    ],
    seeAlso: [
      'Renaissance artists who were also part-time spies',
      'The colour that nearly started a war',
      'Papal commissions rejected for being "too much"',
    ],
  },
  '1920s bootlegger': {
    prefix: '',
    nation: 'American',
    occupations: ['Bootlegger', 'Entrepreneur', 'Speakeasy Operator', 'Jazz Patron'],
    earlyLifeTemplates: [
      'Growing up on the rough streets of Chicago, young {name} learned that the real money wasn\'t in honest work — it was in knowing which cop to pay off.',
      '{name} got their start running errands for a small-time gang, distinguishing themselves through punctuality and an uncanny ability to hide things in improbable places.',
      'The child of immigrants, {name} swore they\'d make it big. Their first business venture — selling "medicinal" tonic water — was shut down for being suspiciously delicious.',
    ],
    careerTemplates: [
      'By {year}, {name} controlled the flow of {product} through three states, using a fleet of modified milk trucks and a network of tunnels that would later confuse urban archaeologists.',
      '{name}\'s speakeasy, "The {adjective} {animal}," became legendary for its jazz bands, its password system involving live poultry, and the fact that it was never raided — rumour had it the police chief was a regular.',
      'During the height of Prohibition, {name} orchestrated what newspapers called "The Great {city} Heist" — 12,000 bottles of whisky vanished from a government warehouse and reappeared at a wedding the next day.',
    ],
    controversyTemplates: [
      'Rival bootlegger "Two-Fingers" Malone once put a bounty on {name}\'s hat. {name} responded by mailing Malone a different hat every week for a year, each one containing increasingly passive-aggressive notes.',
      '{name} was brought to trial in {year2} but the case collapsed when the key witness — a parrot trained to repeat incriminating conversations — refused to testify, simply repeating "pretty bird" for three hours.',
    ],
    legacyTemplates: [
      'After Prohibition ended, {name} went legit, opening a chain of {business} that stayed in the family for three generations. The secret ingredient in the house special remains a closely guarded mystery.',
      '{name} retired to a quiet life in {retirementPlace}, where neighbours described them as "charming, generous, and oddly knowledgeable about boat registration loopholes."',
    ],
    seeAlso: [
      'Prohibition-era cocktails that should have stayed illegal',
      'The Great Milk Truck Conspiracy',
      'Speakeasy passwords that went too far',
      'Jazz musicians who were definitely also criminals',
    ],
  },
  'Medieval alchemist': {
    prefix: 'Master',
    nation: 'Bohemian',
    occupations: ['Alchemist', 'Herbalist', 'Court Advisor', 'Professional Mystery'],
    earlyLifeTemplates: [
      'Born during a thunderstorm that locals insisted was an omen, {name} spent their childhood collecting odd-smelling herbs and asking uncomfortable questions about the nature of matter.',
      'Apprenticed to the court alchemist of {kingdom}, young {name} was assigned the task of turning lead into gold. They failed, but accidentally invented a surprisingly effective hair tonic.',
      '{name} claimed to have learned alchemy from a mysterious traveller who spoke in riddles and smelled faintly of sulphur. The traveller was later revealed to be a cheese merchant with a flair for drama.',
    ],
    careerTemplates: [
      'In {year}, {name} published "On the Transmutation of {substance}," a treatise so dense and cryptic that scholars are still arguing about whether it contains actual wisdom or is just very elaborate doodling.',
      'Commissioned by {monarch} to discover the Elixir of Life, {name} instead produced a beverage that turned the royal physician\'s hair bright green for three months. The monarch was reportedly amused.',
      '{name} claimed to have created a Philosopher\'s Stone small enough to fit in a thimble. When asked to demonstrate, they explained the stone was "shy" and would only perform before an audience of exactly seven people during a full moon.',
    ],
    controversyTemplates: [
      'The Church investigated {name} for "unnatural experiments" after a neighbour reported seeing coloured smoke emerging from the laboratory chimney in patterns that "seemed to spell things."',
      'Rival alchemist Heinrich von Fraud accused {name} of fabricating results. {name} challenged von Fraud to an alchemical duel, which ended inconclusively when both contestants\' mixtures cancelled each other out and produced a very pleasant tea.',
    ],
    legacyTemplates: [
      'Though {name} never turned lead into gold, their detailed notebooks on {legacyField} influenced later scientists. Half the notes are in code that remains unbroken; the other half appear to be shopping lists.',
      '{name} vanished in {deathYear} under circumstances that invited much speculation. Some say they achieved the Great Work and ascended; others note they had an unpaid tab at the local tavern.',
    ],
    seeAlso: [
      'Alchemists who accidentally invented food',
      'The Transmutation That Was Actually Just Paint',
      'Royal courts that employed wizards (badly)',
    ],
  },
  'Cold War spy': {
    prefix: 'Agent',
    nation: '', // ambiguous
    occupations: ['Intelligence Officer', 'Diplomat (allegedly)', 'Defector (maybe)', 'Cipher Expert'],
    earlyLifeTemplates: [
      'Recruited at university for their exceptional skill at {skill}, {name} was trained in the art of invisible ink, dead drops, and maintaining a cover story while three drinks deep.',
      'Born in a country whose name changed three times during their childhood, {name} learned early that identity was a flexible concept.',
      'Little is known about {name}\'s childhood — and that\'s exactly how they wanted it. The one known fact: they once beat a chess grandmaster while simultaneously knitting a scarf.',
    ],
    careerTemplates: [
      'Stationed in {city} under the cover of a {coverJob}, {name} reportedly ran a network of informants that included a ballerina, a baker, and a diplomat\'s cat. The cat was considered the most reliable.',
      'Operation {opName}, masterminded by {name}, involved the exchange of microfilm hidden in a hollow chess piece during a tournament that {name} won — though whether for intelligence purposes or genuine skill remains debated.',
      'In {year}, {name} orchestrated the defection of a high-ranking {adjective} scientist using nothing but a forged opera ticket and a convincingly faked love letter.',
    ],
    controversyTemplates: [
      'Was {name} a double agent? A triple agent? The declassified file from {year2} has more redactions than text, and the surviving paragraphs raise more questions than they answer.',
      'The "{city} Incident" of {year2} — in which {name} was allegedly involved — remains classified. Unofficial accounts mention a briefcase, a parrot, and an improbable number of umbrellas.',
    ],
    legacyTemplates: [
      '{name} retired to a quiet life writing spy novels under a pseudonym. Critics noted the plots were "implausible" — readers who actually worked in intelligence reportedly found them uncomfortably accurate.',
      'A single photograph of {name} exists in the public record. In it, they are holding a newspaper that, upon close examination, contains a crossword puzzle whose answers form a coded message no one has ever deciphered.',
    ],
    seeAlso: [
      'The Spy Who Came In From The Cold (and forgot their hat)',
      'Dead drops that were actually just litter',
      'Diplomatic immunity: the ultimate cheat code',
    ],
  },
  'Ancient philosopher': {
    prefix: '',
    nation: 'Greek',
    occupations: ['Philosopher', 'Teacher', 'Public Nuisance', 'Oracle Consultant'],
    earlyLifeTemplates: [
      'Born in Athens during a particularly argumentative era, {name} allegedly emerged from the womb already frowning and asking what the midwife meant by "done."',
      'As a child, {name} reportedly asked their teacher "but what is learning?" — beginning a line of questioning that lasted 40 years and annoyed everyone in the agora.',
      'The Oracle at Delphi was consulted about the young {name}. The oracle replied "this one will ask many questions." The delegation demanded a refund for vagueness.',
    ],
    careerTemplates: [
      '{name} founded the School of {school}, whose teachings can be summarised as: "everything you think you know is wrong, and so is this statement." Students found it both enlightening and deeply frustrating.',
      'In {year} BCE, {name} debated the prominent sophist {sophist} in the public square. The debate lasted three days and resolved nothing, which everyone agreed was the point.',
      'The government of Athens once offered {name} a position as state philosopher. {name} responded by asking "what is a state?" and "what is a position?" and eventually "what is a philosopher?" The offer was withdrawn.',
    ],
    controversyTemplates: [
      '{name} was put on trial for "corrupting the youth" and "introducing new ideas." The defence — "define corrupting" — was technically brilliant but politically disastrous.',
      'Rival philosopher {rival} once challenged {name} to a foot race to settle a metaphysical dispute. {name} argued that movement was an illusion, then lost the race anyway.',
    ],
    legacyTemplates: [
      'None of {name}\'s writings survive. Everything we know comes from students\' notes, which famously contradict each other on every major point. Scholars consider this perfectly appropriate.',
      '{name} died peacefully at age {deathAge}, reportedly while asking the attending physician "but what does it mean, to die?" The physician, who had heard this sort of thing before, simply shrugged.',
    ],
    seeAlso: [
      'Philosophical arguments that ended in fistfights',
      'The Symposium That Got Weird',
      'Greek philosophers by number of enemies made',
    ],
  },
  'Wild West outlaw': {
    prefix: '',
    nation: 'American',
    occupations: ['Outlaw', 'Gunslinger', 'Cattle Rustler (alleged)', 'Folk Hero'],
    earlyLifeTemplates: [
      'Born in a one-horse town so small the horse was rented, {name} learned to ride before they could walk and to lie about their age before they could talk.',
      'The youngest of {siblings} children, {name} decided early that honest farm work was not the path. The path was, specifically, a dirt road leading away from the farm at high speed.',
      'Legend says {name} could shoot a playing card out of the air at 50 paces. The less exciting truth: they could, but only after the card had already landed.',
    ],
    careerTemplates: [
      '{name} was wanted in {territories} territories for crimes including, but not limited to: stagecoach interruption, cattle creative-reallocation, and "general nuisance with a harmonica."',
      'The {name} Gang pulled off the infamous {town} Bank Job of {year}, making off with $12,000 in gold and, for reasons never explained, the bank manager\'s collection of decorative spoons.',
      'During a standoff in {town}, Sheriff {sheriff} demanded {name} surrender. {name} reportedly responded, "You\'ll have to define surrender first," then escaped through a window that definitely hadn\'t been there before.',
    ],
    controversyTemplates: [
      'Historians debate whether {name} was a cold-blooded criminal or a misunderstood folk hero. The surviving wanted posters, which describe them as "charming but slippery," support both interpretations.',
      'The Pinkerton Detective Agency spent {amount} pursuing {name}, who evaded capture by doing absolutely nothing for two months while the agents chased elaborate false leads.',
    ],
    legacyTemplates: [
      'After mysteriously disappearing in {deathYear}, {name} became the subject of countless dime novels, each one less accurate than the last. The dime novels outsold actual history books 3 to 1.',
      'To this day, treasure hunters search for {name}\'s hidden loot, supposedly buried "where the coyote howls at the crooked pine." There are approximately 40,000 crooked pines in the region.',
    ],
    seeAlso: [
      'Outlaws who were actually quite polite',
      'The Great Spoon Heist Mystery',
      'Wanted: Dead or Alive (or mildly inconvenienced)',
    ],
  },
  'Jazz Age musician': {
    prefix: '',
    nation: 'American',
    occupations: ['Musician', 'Bandleader', 'Improvisational Philosopher', 'Night Owl'],
    earlyLifeTemplates: [
      'Born in New Orleans to a family that considered music "the respectable alternative to street performing," {name} picked up the {instrument} at age 6 and never put it down — figuratively, at least.',
      'As a teenager, {name} sneaked into jazz clubs by claiming to be the cousin of whichever musician was on stage. It worked surprisingly often; the jazz community was loosely defined.',
      'Growing up in a boarding house for travelling musicians, {name} absorbed every style that passed through: blues, ragtime, gospel, and a genre one boarder called "don\'t wake the landlady."',
    ],
    careerTemplates: [
      'By {year}, {name} was headlining at the {club} in Harlem, known for performances that started at midnight and ended when the audience admitted they had jobs to go to.',
      '{name} recorded the legendary track "{song}" in a single take at 3 AM after the producer bet $5 it couldn\'t be done. The recording captures a moment where {name} audibly laughs in the middle of a solo.',
      '{name}\'s rivalry with fellow musician {rival} was the stuff of legend — they would challenge each other to "cutting contests" where musicians traded increasingly impossible solos until someone\'s instrument caught fire (this happened twice).',
    ],
    controversyTemplates: [
      '{name} was briefly banned from three states for "musical indecency" after a performance that allegedly caused spontaneous dancing among people who had previously claimed to dislike music.',
      'The "{incident}" of {year2} — in which {name} reportedly performed for 14 hours straight, stopping only because the piano needed to be taken to hospital — was officially denied but widely celebrated.',
    ],
    legacyTemplates: [
      '{name} influenced generations of musicians, many of whom cited the same impossible story: "I saw {name} once, and I still don\'t know how they did it."',
      'Retiring from performing in {deathYear}, {name} spent their final years teaching young musicians at a school where the curriculum consisted entirely of "feel it, then play it." Graduation rates were low but results were spectacular.',
    ],
    seeAlso: [
      'Jazz solos that broke physics',
      'The night the piano caught fire (both times)',
      'Musicians who definitely didn\'t sleep enough',
    ],
  },
};

const FALLBACK_ERA = 'Victorian inventor';

// ── Helper functions ──

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function yearRange(): [number, number] {
  const birth = 1450 + Math.floor(Math.random() * 400);
  const death = birth + 40 + Math.floor(Math.random() * 40);
  return [birth, death];
}

function generateArticle(name: string, eraKey: string, trait: string): string {
  const era = ERA_DATA[eraKey] ?? ERA_DATA[FALLBACK_ERA];
  const [birth, death] = yearRange();
  const prefix = era.prefix ? `${era.prefix} ` : '';
  const fullName = `${prefix}${name}`;
  const nationality = era.nation;
  const occupation = pick(era.occupations);

  // Build infobox
  const infobox = [
    `| name         = ${fullName}`,
    `| image        = Portrait_pending.jpg`,
    `| caption      = Artist\'s impression (nobody could agree on the nose)`,
    `| birth_date   = ${birth}`,
    `| birth_place  = ${pick(['Somewhere', 'Probably', 'Disputed', 'Unknown but charming'])}`,
    `| death_date   = ${death}`,
    `| death_place  = ${pick(['Under mysterious circumstances', 'In bed, allegedly', 'Mid-sentence', 'The records are unclear'])}`,
    `| nationality  = ${nationality}`,
    `| occupation   = ${occupation}`,
    `| known_for    = ${trait || pick(['Being impossible to ignore', 'Changing everything (citation needed)', 'That thing with the badger'])}`,
  ].join('\n');

  // Fill templates
  const fill = (template: string): string =>
    template
      .replace(/\{name\}/g, fullName)
      .replace(/\{era\}/g, eraKey)
      .replace(/\{year\}/g, String(birth + 18 + Math.floor(Math.random() * 15)))
      .replace(/\{year2\}/g, String(birth + 25 + Math.floor(Math.random() * 15)))
      .replace(/\{deathYear\}/g, String(death))
      .replace(/\{invention\}/g, pick(['Automatic Teacup Reheater', 'Pneumatic Trouser Press', 'Steam-Powered Letter Opener', 'Electric Conversation Starter', 'Hydraulic Toast Turner']))
      .replace(/\{field\}/g, pick(['domestic engineering', 'speculative physics', 'recreational chemistry', 'applied whimsy']))
      .replace(/\{discovery\}/g, pick(['reverse evaporation', 'selective gravity', 'audible magnetism', 'spontaneous organisation']))
      .replace(/\{principle\}/g, pick(['Elastic Certainty', 'Recursive Disbelief', 'Compensatory Confusion', 'Progressive Approximation']))
      .replace(/\{topic\}/g, pick(['The Nature of Damp', 'Applied Speculation', 'On the Classification of Smells', 'A Theory of Almost Everything']))
      .replace(/\{modernField\}/g, pick(['vibration science', 'nonlinear thinking', 'intuitive engineering', 'creative misinterpretation']))
      .replace(/\{scene\}/g, pick(['Inevitability of Tuesday', 'Triumph of the Overconfident', 'Allegory of Lunch', 'Resignation of the Radishes']))
      .replace(/\{artwork\}/g, pick(['The Snickering Cherub', 'Madonna of the Suspicious Expression', 'The Reluctant Martyr']))
      .replace(/\{technique\}/g, pick(['sfumato-but-make-it-sarcastic', 'aggressive chiaroscuro', 'philosophical impasto', 'passive-aggressive perspective']))
      .replace(/\{product\}/g, pick(['fine Canadian whisky', 'artisanal gin', 'medicinal brandy', 'honest-to-goodness corn liquor']))
      .replace(/\{adjective\}/g, pick(['Laughing', 'Crooked', 'Midnight', 'Secret', 'Perplexed']))
      .replace(/\{animal\}/g, pick(['Otter', 'Pheasant', 'Fox', 'Badger', 'Flamingo']))
      .replace(/\{city\}/g, pick(['Detroit', 'Kansas City', 'New Orleans', 'Brooklyn', 'Paris', 'Berlin', 'Cairo']))
      .replace(/\{business\}/g, pick(['laundromats', 'ice cream parlours', 'pet grooming salons', 'jazz clubs']))
      .replace(/\{retirementPlace\}/g, pick(['Florida', 'a small coastal town', 'an undisclosed location', 'Argentina, for some reason']))
      .replace(/\{kingdom\}/g, pick(['Bohemia', 'Transylvania', 'Wallachia']))
      .replace(/\{substance\}/g, pick(['Turnips into Enlightenment', 'Regret into Marmalade', 'Common Pebbles into Philosophical Insight']))
      .replace(/\{monarch\}/g, pick(['King Rudolf II', 'Emperor Ferdinand', 'Duke Albrecht the Mildly Interested']))
      .replace(/\{legacyField\}/g, pick(['botanical extraction', 'atmospheric pressure', 'substance interaction', 'early chemistry']))
      .replace(/\{skill\}/g, pick(['remembering faces', 'forgetting names', 'blending into wallpaper', 'speaking five languages badly']))
      .replace(/\{coverJob\}/g, pick(['cultural attaché', 'import/export consultant', 'jazz critic', 'rare book dealer']))
      .replace(/\{opName\}/g, pick(['Nightjar', 'Velvet Glove', 'Paper Crane', 'Reluctant Sunrise']))
      .replace(/\{school\}/g, pick(['Perpetual Uncertainty', 'Aggressive Sincerity', 'Calculated Ambiguity', 'The Strategic Shrug']))
      .replace(/\{sophist\}/g, pick(['Protagoras', 'Gorgias', 'Hippias', 'Thrasymachus']))
      .replace(/\{rival\}/g, pick(['Aristippus the Unpleasant', 'Diodorus the Argumentative', 'Crates the Surprisingly Buff']))
      .replace(/\{deathAge\}/g, String(death - birth))
      .replace(/\{siblings\}/g, String(3 + Math.floor(Math.random() * 9)))
      .replace(/\{territories\}/g, String(2 + Math.floor(Math.random() * 5)))
      .replace(/\{town\}/g, pick(['Dry Gulch', 'Redemption', 'Broken Spur', 'Tumbleweed Junction']))
      .replace(/\{sheriff\}/g, pick(['Jebediah Stone', 'Marshal "Big Hat" Callahan', 'Sheriff Pensive McCree']))
      .replace(/\{amount\}/g, pick(['$3,000', '$8,500', 'a truly embarrassing sum of money']))
      .replace(/\{instrument\}/g, pick(['trumpet', 'saxophone', 'clarinet', 'piano', 'trombone']))
      .replace(/\{club\}/g, pick(['Cotton Club', 'Savoy Ballroom', 'Blue Note', 'The Velvet Room']))
      .replace(/\{song\}/g, pick(["Don\'t Ask Me, I\'m Just the Piano Player", 'Tuesday at 4 AM Blues', 'The Moon Looked Better Yesterday', 'I Swear I Left My Heart in Cleveland']))
      .replace(/\{incident\}/g, pick(['Marathon Session', 'Great Clarinet Standoff', 'Night the Bass Player Proposed to the Piano']));

  const earlyLife = fill(pick(era.earlyLifeTemplates));
  const career = fill(pick(era.careerTemplates));
  const controversy = fill(pick(era.controversyTemplates));
  const legacy = fill(pick(era.legacyTemplates));
  const seeAlso = era.seeAlso.map(s => `* [[${s}]]`).join('\n');

  const citations = pick([
    ['[1]', 'Archives of Dubious History, Vol. 3, pp. 127–129.'],
    ['[2]', 'Personal correspondence, currently housed in a shoebox.'],
    ['[3]', 'This citation was added for credibility and has not been verified.'],
    ['[4]', 'Oral tradition — the teller seemed very confident.'],
  ]);

  return `{{Infobox person
${infobox}
}}

'''${fullName}''' (${birth} – ${death}) was a ${nationality} ${occupation.toLowerCase()} best known for ${trait || 'their remarkable and somewhat baffling contributions to their field'}.${citations[0]}

== Early Life ==
${earlyLife}${citations[1]}

== Career ==
${career}${citations[2]}

== Controversies ==
${controversy}${citations[3]}

== Legacy ==
${legacy}

== See Also ==
${seeAlso}

''This article is part of the '''Myth Project''', a collection of biographies that are almost certainly not true but absolutely should be.''`;
}

// ── Component ──

export default function MythGenerator() {
  const [name, setName] = useState('');
  const [era, setEra] = useState('');
  const [trait, setTrait] = useState('');
  const [wikiText, setWikiText] = useState('');
  const [generatedName, setGeneratedName] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const eras = Object.keys(ERA_DATA);

  const handleGenerate = async () => {
    setLoading(true);
    setCopied(false);
    // Simulate API delay
    await new Promise(r => setTimeout(r, 800));
    const article = generateArticle(name, era, trait);
    setWikiText(article);
    setGeneratedName(name);
    setLoading(false);
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(wikiText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShare = async () => {
    if (navigator.share) {
      await navigator.share({
        title: `Myth: ${generatedName}`,
        text: wikiText.substring(0, 200) + '...',
      });
    } else {
      handleCopy();
    }
  };

  return (
    <div data-theme="retro" className="min-h-screen">
      {/* ── Hero ── */}
      <header className="text-center py-12 px-4 bg-base-200 border-b border-base-300">
        <h1 className="text-5xl font-serif font-bold tracking-tight mb-3">
          Myth
        </h1>
        <p className="text-lg text-base-content/70 max-w-md mx-auto">
          Your friend, as a {pick(eras.map(e => ERA_DATA[e]?.occupations?.[0]).filter(Boolean))} nobody&apos;s heard of.
        </p>
        <p className="text-sm text-base-content/50 mt-2">
          The free encyclopedia that anyone can fabricate.
        </p>
      </header>

      {/* ── Input form ── */}
      <section className="max-w-lg mx-auto px-4 py-8">
        <div className="card bg-base-200 shadow-sm">
          <div className="card-body gap-5">
            <div className="form-control">
              <label className="label">
                <span className="label-text font-medium">Friend&apos;s Name</span>
              </label>
              <input
                type="text"
                placeholder="e.g. Sarah Chen"
                className="input input-bordered w-full"
                value={name}
                onChange={e => setName(e.target.value)}
              />
            </div>

            <div className="form-control">
              <label className="label">
                <span className="label-text font-medium">Historical Era</span>
              </label>
              <select
                className="select select-bordered w-full"
                value={era}
                onChange={e => setEra(e.target.value)}
              >
                <option disabled value="">Pick an era…</option>
                {eras.map(e => (
                  <option key={e} value={e}>{e}</option>
                ))}
              </select>
            </div>

            <div className="form-control">
              <label className="label">
                <span className="label-text font-medium">Quirk / Claim to Fame</span>
                <span className="label-text-alt">optional</span>
              </label>
              <input
                type="text"
                placeholder="e.g. believed cats were spies"
                className="input input-bordered w-full"
                value={trait}
                onChange={e => setTrait(e.target.value)}
              />
            </div>

            <button
              className="btn btn-primary btn-block mt-2"
              disabled={!name || !era || loading}
              onClick={handleGenerate}
            >
              {loading ? (
                <>
                  <span className="loading loading-spinner loading-sm"></span>
                  Summoning the archives…
                </>
              ) : (
                'Write Their History'
              )}
            </button>
          </div>
        </div>
      </section>

      {/* ── Article output ── */}
      {wikiText && (
        <section className="max-w-3xl mx-auto px-4 pb-16">
          {/* Share bar */}
          <div className="flex gap-2 mb-4 justify-end">
            <button className="btn btn-sm btn-ghost" onClick={handleCopy}>
              {copied ? '✓ Copied!' : '📋 Copy'}
            </button>
            <button className="btn btn-sm btn-ghost" onClick={handleShare}>
              🔗 Share
            </button>
          </div>

          {/* Wikipedia-style output */}
          <article className="bg-white border border-base-300 p-6 md:p-10 font-serif text-base-content leading-relaxed shadow-sm">
            <pre className="whitespace-pre-wrap font-serif text-[15px] leading-relaxed bg-transparent p-0 border-0">
              {wikiText}
            </pre>
          </article>
        </section>
      )}

      {/* ── Footer ── */}
      <footer className="text-center py-6 text-sm text-base-content/40 border-t border-base-300">
        Myth · Part of the <span className="italic">Probably Not True</span> project · {new Date().getFullYear()}
      </footer>
    </div>
  );
}