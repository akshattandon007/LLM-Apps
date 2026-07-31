import { useState } from 'react';
import Head from 'next/head';

type FormData = {
  recipientName: string;
  relationship: string;
  interests: string;
  sharedMemory: string;
  makesThemLaugh: string;
};

type GiftResult = {
  giftIdea: string;
  poem: string;
  whyPerfect: string;
};

const mockGifts: Record<string, GiftResult> = {
  'fishing': {
    giftIdea: 'A custom leather-bound fishing journal with the coordinates of your favorite spot embossed on the cover. Comes with a handwritten-style note: Every cast is a conversation, Dad. Here\'s to the next one.',
    poem: 'The river bends, the line extends,\nA father\'s patience never ends.\nEach cast a lesson, each catch a cheer,\nThese are the moments we hold most dear.',
    whyPerfect: 'Because it combines his love for fishing with your shared memories, making it more than just a gift - it\'s a keepsake of your bond.'
  },
  'gardening': {
    giftIdea: 'A personalized garden stone engraved with her grandmother\'s favorite flower quote, plus a packet of vintage zinnia seeds — the same variety she grew when you were little.',
    poem: 'In soil she finds her quiet place,\nWhere flowers bloom with patient grace.\nEach petal holds a memory,\nOf love that grows eternally.',
    whyPerfect: 'It connects her gardening passion with family history, making the garden even more meaningful with each season.'
  },
  'foodie': {
    giftIdea: 'A custom cookbook filled with recipes from your favorite shared meals, plus blank pages for future culinary adventures together.',
    poem: 'The kitchen hums with laughter bright,\nAs flavors dance from noon to night.\nEach recipe a story told,\nOf friendship seasoned warm with gold.',
    whyPerfect: 'It celebrates your shared love of food while creating space for new food memories together.'
  },
  'music': {
    giftIdea: 'A vintage record player with a custom vinyl featuring recordings of songs that mark important moments in your relationship.',
    poem: 'The needle drops, the music flows,\nEach note a memory that glows.\nFrom first dance to last goodnight,\nThese are the songs that feel just right.',
    whyPerfect: 'It combines their love of music with the soundtrack of your relationship in a tangible, nostalgic format.'
  },
  'travel': {
    giftIdea: 'A handmade travel journal with maps of places you\'ve visited together, plus blank pages for future adventures.',
    poem: 'The open road, the distant shore,\nEach journey makes us want more.\nNot just the places that we see,\nBut who we are when we are free.',
    whyPerfect: 'It captures your shared wanderlust while providing space to document new adventures together.'
  }
};

export default function Home() {
  const [step, setStep] = useState<'hero' | 'form' | 'loading' | 'result'>('hero');
  const [formData, setFormData] = useState<FormData>({
    recipientName: '',
    relationship: '',
    interests: '',
    sharedMemory: '',
    makesThemLaugh: ''
  });
  const [result, setResult] = useState<GiftResult | null>(null);
  const [theme, setTheme] = useState<'cupcake' | 'retro'>('cupcake');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setStep('loading');
    
    // Simulate API call with timeout
    setTimeout(() => {
      // Simple mock logic - in a real app this would call an API
      const personaType = 
        formData.interests.toLowerCase().includes('fish') ? 'fishing' :
        formData.interests.toLowerCase().includes('garden') ? 'gardening' :
        formData.interests.toLowerCase().includes('food') ? 'foodie' :
        formData.interests.toLowerCase().includes('music') ? 'music' : 'travel';
      
      setResult(mockGifts[personaType]);
      setStep('result');
    }, 2000);
  };

  return (
    <div data-theme={theme} className="min-h-screen">
      <Head>
        <title>The Gift - Personalized Gift Ideas</title>
        <meta name="description" content="Generate heartfelt, personalized gift ideas" />
      </Head>

      <main className="container mx-auto px-4 py-8">
        {step === 'hero' && (
          <div className="hero min-h-[60vh] bg-base-200 rounded-lg">
            <div className="hero-content text-center">
              <div className="max-w-md">
                <h1 className="text-5xl font-bold">The Gift</h1>
                <p className="py-6">
                  Describe someone special and we'll create a personalized gift idea 
                  that shows how well you know them — plus a heartfelt poem or story.
                </p>
                <div className="flex gap-4 justify-center">
                  <button 
                    className="btn btn-primary"
                    onClick={() => setStep('form')}
                  >
                    Get Started
                  </button>
                  <div className="dropdown dropdown-end">
                    <div tabIndex={0} role="button" className="btn">
                      Theme
                    </div>
                    <ul tabIndex={0} className="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-52">
                      <li><button onClick={() => setTheme('cupcake')}>Cupcake</button></li>
                      <li><button onClick={() => setTheme('retro')}>Retro</button></li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {step === 'form' && (
          <div className="max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold mb-6">Tell us about them</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="form-control">
                <label className="label">
                  <span className="label-text">Recipient's Name</span>
                </label>
                <input 
                  type="text" 
                  name="recipientName"
                  value={formData.recipientName}
                  onChange={handleInputChange}
                  placeholder="e.g. Dad" 
                  className="input input-bordered w-full" 
                  required 
                />
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">Your Relationship</span>
                </label>
                <input 
                  type="text" 
                  name="relationship"
                  value={formData.relationship}
                  onChange={handleInputChange}
                  placeholder="e.g. Son" 
                  className="input input-bordered w-full" 
                  required 
                />
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">What They Love</span>
                </label>
                <textarea 
                  name="interests"
                  value={formData.interests}
                  onChange={handleInputChange}
                  className="textarea textarea-bordered h-24" 
                  placeholder="Their hobbies, passions, favorite things..."
                  required
                ></textarea>
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">A Shared Memory</span>
                </label>
                <textarea 
                  name="sharedMemory"
                  value={formData.sharedMemory}
                  onChange={handleInputChange}
                  className="textarea textarea-bordered h-24" 
                  placeholder="A special moment you've shared..."
                  required
                ></textarea>
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">What Makes Them Laugh</span>
                </label>
                <textarea 
                  name="makesThemLaugh"
                  value={formData.makesThemLaugh}
                  onChange={handleInputChange}
                  className="textarea textarea-bordered h-24" 
                  placeholder="Their sense of humor, inside jokes..."
                  required
                ></textarea>
              </div>

              <div className="flex justify-end gap-4 pt-4">
                <button 
                  type="button" 
                  className="btn btn-ghost"
                  onClick={() => setStep('hero')}
                >
                  Back
                </button>
                <button type="submit" className="btn btn-primary">
                  Generate Gift Idea
                </button>
              </div>
            </form>
          </div>
        )}

        {step === 'loading' && (
          <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
            <span className="loading loading-spinner loading-lg"></span>
            <p className="text-xl">Creating your personalized gift idea...</p>
          </div>
        )}

        {step === 'result' && result && (
          <div className="max-w-2xl mx-auto">
            <div className="card bg-base-100 shadow-xl">
              <div className="card-body">
                <h2 className="card-title text-3xl mb-4">For {formData.recipientName}</h2>
                
                <div className="space-y-6">
                  <div>
                    <h3 className="text-xl font-semibold mb-2">Gift Idea</h3>
                    <p className="whitespace-pre-line">{result.giftIdea}</p>
                  </div>

                  <div>
                    <h3 className="text-xl font-semibold mb-2">Poem</h3>
                    <div className="bg-base-200 p-4 rounded-lg">
                      <p className="whitespace-pre-line italic">{result.poem}</p>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-xl font-semibold mb-2">Why This Gift Is Perfect</h3>
                    <p className="whitespace-pre-line">{result.whyPerfect}</p>
                  </div>
                </div>

                <div className="card-actions justify-end mt-6">
                  <button 
                    className="btn btn-primary"
                    onClick={() => {
                      navigator.clipboard.writeText(`${result.giftIdea}\n\n${result.poem}\n\n${result.whyPerfect}`);
                      alert('Copied to clipboard!');
                    }}
                  >
                    Copy
                  </button>
                  <button 
                    className="btn btn-secondary"
                    onClick={() => {
                      setStep('form');
                      setResult(null);
                    }}
                  >
                    Generate Another
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
