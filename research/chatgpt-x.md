[chatgpt] tool:web.run

Sources:
  https://www.wemakedevs.org/hackathons/falkordb/rules
  https://www.wemakedevs.org/blogs/how-to-build-an-agent-that-reasons-over-a-graph
  https://in.linkedin.com/company/falkordb/
  https://www.linkedin.com/posts/aditya-arnav-76a0222a1_graphhacks-falkordb-aiagents-activity-7511814871928201216-bXmQ
  https://www.linkedin.com/posts/wemakedevs_were-giving-away-an-iphone-18-pro-a-ps5-activity-7511394933858246656-3u4W
  https://github.com/howdycarter/graph-hacks-falkordb-2026/blob/main/README.md
  https://github.com/swarnnim/trace
  https://telemetr.io/en/channels/1579486688-wemakedevs/posts
  https://twstalker.com/g_korland
  https://oa.linkedin.com/company/falkordb
  https://ac.linkedin.com/company/falkordb/
  https://ne.linkedin.com/company/falkordb
  https://so.linkedin.com/company/falkordb/
  https://na.linkedin.com/company/falkordb/
  https://bt.linkedin.com/company/falkordb/
  https://er.linkedin.com/company/falkordb/
  https://ea.linkedin.com/company/falkordb
  https://ug.linkedin.com/company/falkordb/
  https://ao.linkedin.com/company/falkordb/
  https://iq.linkedin.com/company/falkordb/
[gpt-5-6 - 15.0s - https://chatgpt.com/c/6ad46f80-44dc-83ee-b907-a7ecb55a0794]
## FalkorDB Graph Hacks (Oct 15–18, 2026)

The official [WeMakeDevs hackathon rules](https://www.wemakedevs.org/hackathons/falkordb/rules) define the challenge as **“Context for AI Agents”**: build AI agents that use a graph for connected context, persistent memory, or company knowledge. The event is online, with a $20,000 prize pool. <Cite refs={["turn351435search0","turn351435search1"]}/>

### What participants are building

- **Trace:** A research agent with graph-native memory. It stores episodic memory, semantic facts, and multi-agent shared state in FalkorDB, then exposes the graph traversal behind each answer. [GitHub repository](https://github.com/swarnnim/trace). <Cite refs={["turn351435search5"]}/>
- **Persistent, explainable memory:** Aditya Arnav's team describes building memory that survives sessions, tracks changed or superseded facts, isolates users, and preserves provenance. The team emphasizes using FalkorDB as the actual context layer, not an optional add-on. [LinkedIn post](https://www.linkedin.com/posts/aditya-arnav-76a0222a1_graphhacks-falkordb-aiagents-activity-7511814871928201216-bXmQ). <Cite refs={["turn351435search3"]}/>
- **Operational agents:** WeMakeDevs' example project, Blast Radius, diagnoses service outages by traversing dependency graphs to identify affected services, on-call owners, and recent changes. [Technical walkthrough](https://www.wemakedevs.org/blogs/how-to-build-an-agent-that-reasons-over-a-graph). <Cite refs={["turn351435search2"]}/>

### What Guy Korland and Roi Lipman want to see

- **FalkorDB must be essential.** The official rules explicitly reject projects where the graph is merely a visualization layer. Removing FalkorDB should break a central part of the product. [Official rules](https://www.wemakedevs.org/hackathons/falkordb/rules).
- **Agents should reason over relationships, not just retrieve text.** The brief emphasizes multi-hop reasoning, graph algorithms, persistent memory, agent handoffs, and decisions traceable to their source. [WeMakeDevs technical guide](https://www.wemakedevs.org/blogs/how-to-build-an-agent-that-reasons-over-a-graph).
- **Useful, working applications matter.** The rules require a public repository, graph data model, relevant Cypher queries or algorithms, and a demo video. [Submission requirements](https://www.wemakedevs.org/hackathons/falkordb/rules).

**Source limitation:** I found FalkorDB's official announcement and material discussing Guy Korland's team's ideas, but couldn't verify a distinct October 2026 post directly from Guy or Roi specifying additional judging preferences. The points above reflect the published challenge, not invented personal quotes. [FalkorDB announcement](https://in.linkedin.com/company/falkordb/)
