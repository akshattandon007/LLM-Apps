# Flow.md — Execution Trace

```
User runs:  python main.py --call
User runs:  python main.py --simulate [character]
User runs:  python main.py --list
```

---

## main.py — Entry Point

```
main()
  ├── load_dotenv()                       # Optional .env for LLM_API_KEY
  ├── print_header()                      # ASCII banner
  ├── parse sys.argv
  │
  ├── if "--list" / "-l":
  │   └── list_roster()
  │       └── list_characters()           # src/characters.py:32
  │           └── returns sorted list of (key, Character)
  │
  ├── if "--call" / "-c":
  │   ├── character_arg given?
  │   │   ├── Yes → run_conversation(character_arg, simulate=True)
  │   │   └── No  → pick_character_interactive()
  │   │       ├── print roster
  │   │       ├── prompt user for number or name
  │   │       ├── get_character(raw)       # src/characters.py:28
  │   │       └── returns key string or None
  │   │
  │   └── run_conversation(key, simulate=True)
  │       ├── get_character(key)           # return Character or None
  │       ├── Conversation(char)           # src/conversation.py:22
  │       ├── conv.start()                 # → adds greeting as Message
  │       ├── print greeting
  │       ├── [CONVERSATION LOOP]
  │       │   ├── input("You: ")
  │       │   ├── conv.add_user_turn(text) # → Message
  │       │   ├── generate_response(conv, simulate, api_key)
  │       │   │   ├── if simulate or no api_key:
  │       │   │   │   └── _simulate_response(conv)   # templated
  │       │   │   └── else:
  │       │   │       ├── conv.build_system_prompt()
  │       │   │       ├── POST /chat/completions via httpx
  │       │   │       └── return response text
  │       │   ├── conv.add_character_turn(text)
  │       │   ├── extract name from user input (heuristic)
  │       │   │   └── conv.add_key_fact(fact) if found
  │       │   └── print response
  │       └── (loop until user says quit/exit/goodbye)
  │
  ├── if "--simulate" / "-s":
  │   └── run_simulate(character_key)
  │       ├── get_character(key) or random pick
  │       ├── Conversation(char)
  │       ├── conv.start() → greeting
  │       ├── for each predefined prompt (3 turns):
  │       │   ├── conv.add_user_turn(prompt)
  │       │   ├── generate_response(conv, simulate=True)
  │       │   └── conv.add_character_turn(response)
  │       └── print catchphrase + "Call ended"
  │
  └── else (no matching flag):
      └── print usage help
```

---

## File-to-file call chain

```
main.py ─────────────────────────────────────────────────┐
  │                                                      │
  ├── src/characters.py                                  │
  │   ├── list_characters()   → [(key, Character), ...]  │
  │   └── get_character(key)  → Character | None         │
  │                                                      │
  ├── src/models.py                                      │
  │   ├── Character (Pydantic)                           │
  │   ├── CharacterVoice (Pydantic)                      │
  │   ├── Message (Pydantic)                             │
  │   └── ConversationState (Pydantic)                   │
  │       ├── add_message() → Message                    │
  │       └── context_window() → str                     │
  │                                                      │
  ├── src/conversation.py                                │
  │   └── Conversation                                   │
  │       ├── start()              → Message (greeting)  │
  │       ├── add_user_turn()      → Message             │
  │       ├── add_character_turn() → Message             │
  │       ├── build_system_prompt() → str                │
  │       ├── add_key_fact(fact)                         │
  │       └── extract_memory() → [] (stub for v2)        │
  │                                                      │
  └── src/responder.py                                   │
      ├── get_client()     → httpx.Client (singleton)    │
      ├── set_client(c)    → None  (test injection)      │
      ├── _simulate_response(conv) → str                 │
      └── generate_response(conv, simulate, api_key)     │
          → str                                          │
             │                                           │
             └── httpx.Client.post()  (only in live mode)│
```

---

## Data flow per turn (interactive mode)

```
1. User types "Tell me about yourself"
2. conv.add_user_turn("Tell me about yourself")
     → Message(role="user", content="...", turn_number=N)
3. generate_response(conv, simulate=True)
     a. _simulate_response(conv)
         - reads conv.character templates
         - picks random template for this character
         - returns string
4. conv.add_character_turn(response)
     → Message(role="character", content="...", turn_number=N+1)
5. Heuristic name extraction on user input
     - checks "i am ", "my name is " etc.
     - if found, conv.add_key_fact(...)
6. Response printed to terminal
7. Loop back to user input
```

---

## Mode comparison

| Mode       | Network? | API Key Required? | Response Quality            |
|------------|----------|-------------------|-----------------------------|
| --simulate | No       | No                | Templated, charming, fixed  |
| --call     | No       | No                | Same as --simulate          |
| --call + .env | Yes  | Yes               | LLM-generated, deep, dynamic |

The architecture makes simulate mode the default because it always works.
Live LLM mode is strictly opt-in via .env configuration.