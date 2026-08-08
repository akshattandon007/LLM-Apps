export interface Message {
  id: string;
  source: 'whatsapp' | 'imessage' | 'email';
  timestamp: string;
  sender: string;
  group?: string;
  subject?: string;
  content: string;
  thread?: Message[];
}

export const sampleData: Message[] = [
  {
    id: 'wa-1',
    source: 'whatsapp',
    timestamp: '2024-06-10T14:30:00Z',
    sender: 'Priya',
    group: 'Tandon Family',
    content: "Hey everyone! For the Goa trip, I'm thinking ₹8,000 per person should cover flights and 3 nights. Thoughts?",
    thread: [
      {
        id: 'wa-1a',
        source: 'whatsapp',
        timestamp: '2024-06-10T14:35:00Z',
        sender: 'Rahul',
        group: 'Tandon Family',
        content: 'That sounds reasonable. Let me check flight prices from Delhi.',
      },
      {
        id: 'wa-1b',
        source: 'whatsapp',
        timestamp: '2024-06-10T14:42:00Z',
        sender: 'Mom',
        group: 'Tandon Family',
        content: 'I found a nice Airbnb in North Goa. ₹2,500/night for the whole place. Should I book?',
      },
      {
        id: 'wa-1c',
        source: 'whatsapp',
        timestamp: '2024-06-10T14:50:00Z',
        sender: 'Sarah',
        group: 'Tandon Family',
        content: "Let's cap costs at ₹10,000/person max. We still need to budget for food and activities.",
      },
      {
        id: 'wa-1d',
        source: 'whatsapp',
        timestamp: '2024-06-10T15:00:00Z',
        sender: 'Priya',
        group: 'Tandon Family',
        content: "Agreed. Budget ₹10,000/person. Mom, go ahead and book the Airbnb! I'll cover the deposit.",
      },
    ],
  },
  {
    id: 'em-1',
    source: 'email',
    timestamp: '2023-11-05T09:15:00Z',
    sender: 'Mom <mom@family.com>',
    subject: 'Roof contractor - Ace Roofing',
    content: "Hi all, I got a recommendation from Mrs. Sharma for Ace Roofing. She said they did a great job on her terrace waterproofing. I've attached their quote — ₹45,000 for the full roof. Shall we go ahead?",
    thread: [
      {
        id: 'em-1a',
        source: 'email',
        timestamp: '2023-11-05T10:30:00Z',
        sender: 'Dad <dad@family.com>',
        subject: 'Re: Roof contractor - Ace Roofing',
        content: "Let's not jump yet. Get at least 3 quotes before deciding. Also check their GST registration. I'll ask around in the society group too.",
      },
    ],
  },
  {
    id: 'em-2',
    source: 'email',
    timestamp: '2023-11-06T16:45:00Z',
    sender: 'Dad <dad@family.com>',
    subject: 'Roof repair - second quote',
    content: "Mr. Patel from the society recommended 'SolidCraft Solutions'. His brother used them last year. I'm calling them tomorrow for a site visit and estimate. Will keep everyone posted.",
  },
  {
    id: 'im-1',
    source: 'imessage',
    timestamp: '2024-09-01T19:00:00Z',
    sender: 'Anika',
    content: 'Aunt Julie birthday dinner — we need to finalize! Date is Sept 15. Olive Garden at 7pm. Who\'s bringing what?',
    thread: [
      {
        id: 'im-1a',
        source: 'imessage',
        timestamp: '2024-09-01T19:05:00Z',
        sender: 'Rohan',
        content: "I'll bring the cake. Red velvet, her favorite.",
      },
      {
        id: 'im-1b',
        source: 'imessage',
        timestamp: '2024-09-01T19:10:00Z',
        sender: 'Anika',
        content: "Perfect. I'll handle the decorations and party poppers. Someone needs to pick her up.",
      },
    ],
  },
];

export const importOptions = [
  {
    id: 'whatsapp',
    title: 'WhatsApp Export',
    description: 'Upload exported chat history (.txt or .json format) from WhatsApp.',
    formats: '.txt, .json',
    maxSize: '50 MB',
    icon: '💬',
  },
  {
    id: 'imessage',
    title: 'iMessage Export',
    description: 'Import iMessage conversations from your Mac or iPhone backup.',
    formats: '.db, .csv',
    maxSize: '100 MB',
    icon: '✉️',
  },
  {
    id: 'gmail',
    title: 'Gmail API',
    description: 'Connect your Gmail account to import family-related emails automatically.',
    formats: 'OAuth 2.0',
    maxSize: 'Unlimited',
    icon: '📧',
  },
];