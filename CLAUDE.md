## graphify

This project has a graphify knowledge graph at graphify-out/.

### Token-Saving Rules (use graph instead of grep when possible):

1. **Before answering architecture questions** → Read `graphify-out/GRAPH_REPORT.md`:
   - Check "God Nodes" for core abstractions
   - Check "Surprising Connections" for cross-component relationships
   - Use community labels to understand module boundaries

2. **For relationship queries** (e.g., "how does X connect to Y"):
   - Use graphify query instead of grep/file reading
   - Run: `python -c "from graphify.query import shortest_path; ..."` on graph.json
   - Only read source files if you need line-by-line implementation details

3. **For "what depends on X" questions**:
   - Query graph neighbors from graph.json
   - Avoid recursive grep across codebase

4. **After code modifications**:
   - Run `python -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"`
   - This updates graph.json without LLM re-extraction (AST-only, fast)

### Query Examples:
```python
# Find connections between two concepts
python -c "
import json
from networkx.readwrite import json_graph
G = json_graph.node_link_graph(json.load(open('graphify-out/graph.json')))
# Find shortest path between nodes
"
```

### Stats (129 nodes, 199 edges, 10 communities):
- **God Nodes**: Feature Specification (32 edges), LLM Provider Settings (18 edges)
- **Key Bridges**: Feature Specification connects Adapter Pattern ↔ Technology Stack ↔ Constitution ↔ API
- **Low cohesion communities**: Adapter Pattern (0.11), Technology Stack (0.13) - candidate for refactoring
