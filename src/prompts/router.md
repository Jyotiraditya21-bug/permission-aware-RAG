Analyze the user's query and decide the best routing strategy.
Options:
- "no-retrieval-needed": Only for pure conversational greetings (e.g., "hi", "thanks") that require no factual knowledge.
- "decompose": For multi-hop, comparative, or complex queries requiring searches across distinct topics.
- "direct-retrieve": For all other queries, including ambiguous ones. When in doubt, always use this.

Output exactly one of the options above and nothing else.
