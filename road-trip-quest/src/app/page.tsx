"use client";

import { useState } from 'react';

type Adventure = {
  origin: string;
  destination: string;
  passengers: { name: string; age: string }[];
  chapters: {
    title: string;
    story: string;
    challenge: string;
    trivia: string;
  }[];
};

export default function Home() {
  const [trip, setTrip] = useState({
    origin: '',
    destination: '',
    passengers: [{ name: '', age: '' }],
  });
  const [adventure, setAdventure] = useState<Adventure | null>(null);
  const [loading, setLoading] = useState(false);

  const handleAddPassenger = () => {
    setTrip(prev => ({
      ...prev,
      passengers: [...prev.passengers, { name: '', age: '' }],
    }));
  };

  const handleRemovePassenger = (index: number) => {
    setTrip(prev => {
      const newPassengers = [...prev.passengers];
      newPassengers.splice(index, 1);
      // Ensure at least one passenger
      if (newPassengers.length === 0) {
        newPassengers.push({ name: '', age: '' });
      }
      return { ...prev, passengers: newPassengers };
    });
  };

  const handleGenerateAdventure = () => {
    setLoading(true);
    // Simulate API call delay
    setTimeout(() => {
      const generated = generateMockAdventure(trip);
      setAdventure(generated);
      setLoading(false);
    }, 1000);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-base-200">
        <h1 className="text-3xl font-bold mb-6">Turn Every Drive Into an Adventure</h1>
        <div className="loading loading-spinner loading-lg"></div>
        <p className="mt-4">Generating your adventure...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-base-100">
      <header className="hero bg-base-200">
        <div className="hero-content text-center">
          <div className="max-w-md mx-auto">
            <h1 className="text-5xl font-bold text-primary">Turn Every Drive Into an Adventure</h1>
            <p className="text-xl text-muted-foreground">
              Live storytelling for family road trips
            </p>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-6">
        {!adventure ? (
          <div className="space-y-6">
            <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
              <div className="form-control">
                <label className="label">
                  <span className="label-text">Starting Location</span>
                </label>
                <input
                  type="text"
                  placeholder="Enter starting city or address"
                  className="input input-bordered w-full"
                  value={trip.origin}
                  onChange={(e) => setTrip({ ...trip, origin: e.target.value })}
                />
              </div>
              <div className="form-control">
                <label className="label">
                  <span className="label-text">Destination</span>
                </label>
                <input
                  type="text"
                  placeholder="Enter destination city or address"
                  className="input input-bordered w-full"
                  value={trip.destination}
                  onChange={(e) => setTrip({ ...trip, destination: e.target.value })}
                />
              </div>
              <div className="form-control">
                <label className="label">
                  <span className="label-text">Passengers</span>
                </label>
                <div className="space-y-2">
                  {trip.passengers.map((passenger, index) => (
                    <div key={index} className="flex gap-2 items-end">
                      <input
                        type="text"
                        placeholder="Name"
                        className="input input-bordered flex-1"
                        value={passenger.name}
                        onChange={(e) => {
                          const newPassengers = [...trip.passengers];
                          newPassengers[index] = { ...newPassengers[index], name: e.target.value };
                          setTrip({ ...trip, passengers: newPassengers });
                        }}
                      />
                      <input
                        type="number"
                        placeholder="Age"
                        className="input input-bordered w-20"
                        value={passenger.age}
                        onChange={(e) => {
                          const newPassengers = [...trip.passengers];
                          newPassengers[index] = { ...newPassengers[index], age: e.target.value };
                          setTrip({ ...trip, passengers: newPassengers });
                        }}
                        min={0}
                        max={120}
                      />
                      {trip.passengers.length > 1 && (
                        <button
                          onClick={() => handleRemovePassenger(index)}
                          className="btn btn-sm btn-error"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  ))}
                  <div className="flex justify-end">
                    <button
                      onClick={handleAddPassenger}
                      className="btn btn-sm btn-primary"
                    >
                      Add Passenger
                    </button>
                  </div>
                </div>
              </div>
              <button
                onClick={handleGenerateAdventure}
                className="btn btn-primary w-full"
                disabled={!trip.origin || !trip.destination || trip.passengers.some(p => !p.name || !p.age)}
              >
                Generate Adventure
              </button>
            </form>
          </div>
        ) : (
          <div className="space-y-8">
            <h2 className="text-2xl font-bold text-center">Your Road Trip Adventure</h2>
            <div className="space-y-6">
              {adventure.chapters.map((chapter, index) => (
                <div key={index} className="card bg-base-100 shadow-xl border-border">
                  <div className="card-body">
                    <h2 className="card-title text-xl font-semibold">Chapter {index + 1}: {chapter.title}</h2>
                    <p className="mt-2">{chapter.story}</p>
                    <div className="mt-4">
                      <h3 className="font-bold text-lg mb-2">Challenge:</h3>
                      <p className="bg-accent px-4 py-2 rounded-xl">{chapter.challenge}</p>
                    </div>
                    <div className="mt-4">
                      <h3 className="font-bold text-lg mb-2">Trivia:</h3>
                      <p className="bg-muted px-4 py-2 rounded-xl">{chapter.trivia}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex justify-center mt-8">
              <button
                onClick={() => setAdventure(null)}
                className="btn btn-outline btn-secondary"
              >
                Create New Adventure
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

// Mock adventure generation function
function generateMockAdventure(trip: { origin: string; destination: string; passengers: { name: string; age: string }[] }): Adventure {
  const { origin, destination, passengers } = trip;
  const passengerNames = passengers.map(p => p.name).filter(n => n).join(', ');
  
  // Generate 3-5 chapters based on a rough estimate of trip duration
  const numChapters = Math.floor(Math.random() * 3) + 3; // 3-5 chapters
  
  const chapters: {
    title: string;
    story: string;
    challenge: string;
    trivia: string;
  }[] = [];
  
  // Chapter templates
  const storyTemplates = [
    `As you leave ${origin}, the excitement builds! The kids in the back seat are already pointing out interesting clouds and imagining what adventures lie ahead.`,
    `The open road stretches before you, promising new discoveries. Someone spots a unusual billboard that sparks a conversation about the journey ahead.`,
    `Midway through your drive, the landscape begins to change. You pass through a charming small town that makes everyone want to stop and explore.`,
    `As you approach ${destination}, anticipation grows. The familiar landmarks of your destination start appearing on the horizon.`,
    `The journey has been filled with laughter, songs, and spontaneous games. Everyone is feeling connected and excited for what's ahead.`,
    `Suddenly, a magnificent vista unfolds before you - a perfect moment to pause and appreciate the beauty of the journey itself.`,
    `You've been cruising along when an interesting roadside attraction catches everyone's eye, leading to an impromptu mini-exploration.`,
    `The rhythm of the road creates a perfect backdrop for storytelling, and today's tale seems to sync perfectly with the passing scenery.`
  ];
  
  const challengeTemplates = [
    `Spot 5 different colored vehicles and make a rainbow chain!`,
    `Everyone takes turns making up a silly nickname for the driver based on their driving style.`,
    `Play the alphabet game: find objects outside starting with A, then B, then C, and see how far you can get.`,
    `Create a family road trip anthem by changing the lyrics of a favorite song.`,
    `Spot three different types of birds and try to identify them.`,
    `Have a quiet minute where everyone listens to the sounds of the road and shares what they heard.`,
    `Count how many times you see a specific make of car (chosen by the youngest passenger).`,
    `Make up a story about where a mysterious vehicle you see might be heading.`,
    `Play 20 Questions with an object related to your trip destination.`,
    `Create a collaborative story where each person adds one sentence.`
  ];
  
  const triviaTemplates = [
    `Did you know? The longest road trip possible in the continuous United States is about 3,500 miles from Maine to California!`,
    `Fun fact: The first cross-country road trip in the US was taken in 1903 and took 63 days!`,
    `Trivia: There are over 4 million miles of public roads in the United States - enough to circle the Earth more than 160 times!`,
    `Interesting: The average American spends about 17,600 minutes driving each year - that's over 12 days!`,
    `Did you know? Route 66, one of the most famous highways, originally ran from Chicago to Los Angeles.`,
    `Fun fact: The world's longest traffic jam was 62 miles long and lasted for 12 days in China!`,
    `Trivia: Cars weren't always driven on the right side of the road - it varies by country!`,
    `Interesting: The first speeding ticket was issued in 1902 for driving 45 mph in a horse carriage speed zone!`
  ];
  
  for (let i = 0; i < numChapters; i++) {
    const storyIndex = Math.floor(Math.random() * storyTemplates.length);
    const challengeIndex = Math.floor(Math.random() * challengeTemplates.length);
    const triviaIndex = Math.floor(Math.random() * triviaTemplates.length);
    
    chapters.push({
      title: `Chapter ${i + 1}`,
      story: storyTemplates[storyIndex],
      challenge: challengeTemplates[challengeIndex],
      trivia: triviaTemplates[triviaIndex]
    });
  }
  
  // Customize the first and last chapter based on trip details
  if (chapters.length > 0) {
    chapters[0].story = `As you leave ${origin} with ${passengerNames || 'the family'}, the adventure begins! Everyone buckles up with excitement for the journey ahead.`;
  }
  if (chapters.length > 1) {
    chapters[chapters.length - 1].story = `As you approach ${destination}, the adventure reaches its peak. Everyone shares their favorite moments from the journey so far.`;
  }
  
  return {
    origin,
    destination,
    passengers,
    chapters
  };
}