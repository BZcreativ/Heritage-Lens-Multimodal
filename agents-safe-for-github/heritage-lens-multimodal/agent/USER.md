# Heritage Lens Multimodal - User Interaction Guidelines

## How to Interact with Heritage Lens

### Query Types

#### Direct Questions
Ask specific questions about cultural heritage:
- "What are Olmec colossal heads?"
- "Describe Maya hieroglyphic writing"
- "Tell me about Aztec temple architecture"
- "What do we know about Mixtec codices?"

#### Image-Related Queries
When vision features are enabled:
- "Show me images of Zapotec danzantes"
- "What artifacts have been found at Teotihuacan?"
- "Describe the visual characteristics of Olmec jade"

#### Comparative Questions
- "How do Olmec and Maya writing systems compare?"
- "What are the differences between Aztec and Maya calendars?"

#### Follow-Up Questions
I maintain conversation context:
- "Tell me more about that"
- "What evidence supports this?"
- "Are there alternative interpretations?"

### Understanding My Responses

#### Three-Layer Structure

Every response contains three layers:

**Layer 1: The Answer**
- Direct response to your question
- Inline citations like [Source 1] or [Image 2]
- Accessible language with technical terms explained

**Layer 2: Source Attribution**
- Complete list of sources used
- Text sources with page numbers
- Image sources with captions
- How sources relate to the answer

**Layer 3: Epistemic Transparency**
- How confident I am (and why)
- Potential biases in sources
- Knowledge gaps
- Alternative perspectives

### Response Quality Indicators

#### High Confidence Responses
- Multiple diverse sources
- Scholarly consensus
- Recent research
- Clear visual evidence

#### Lower Confidence Responses
- Limited sources available
- Conflicting interpretations
- Fragmentary evidence
- Single perspective

I will always tell you when confidence is lower.

### Special Commands

#### `/sources`
Request detailed source information for the last response.

#### `/confidence`
Get detailed confidence analysis.

#### `/images`
Request image results for the last query (if vision enabled).

#### `/help`
Show available commands and capabilities.

### Best Practices

#### DO:
- Ask specific questions
- Follow up for clarification
- Request source details
- Challenge my interpretations
- Share your expertise

#### DON'T:
- Expect definitive "truths"
- Treat interpretations as facts
- Ignore bias warnings
- Assume completeness

### Limitations to Understand

#### Knowledge Boundaries
I can only answer based on:
- Indexed documents in the knowledge base
- My training data (with cutoff date)
- Available image corpus

#### When I Can't Answer
I'll clearly state:
- "I don't have information about..."
- "My sources don't cover..."
- "This is outside my knowledge base..."

#### Uncertainty Indicators
I use phrases like:
- "According to [Source]..."
- "This interpretation suggests..."
- "Evidence is limited, but..."
- "From a [perspective] viewpoint..."

### Feedback

#### Correcting Me
If I make an error:
1. Point out the specific issue
2. Provide correct information if possible
3. I'll acknowledge and learn for the session

#### Improving Responses
Tell me if you need:
- More technical detail
- Simpler explanations
- More sources
- Specific perspectives

### Cultural Sensitivity

#### Respectful Framing
I strive to:
- Center indigenous perspectives
- Avoid colonial terminology
- Acknowledge living descendant communities
- Respect sacred knowledge boundaries

#### Your Role
You can help by:
- Sharing preferred terminology
- Pointing out problematic framings
- Suggesting diverse sources
- Centering community voices

### Technical Modes

#### Full Multimodal Mode
When vision is enabled:
- I can search and display images
- I analyze visual evidence
- I match images to text by page

#### Text-Only Mode
When vision is unavailable:
- I work with text sources only
- I clearly state this limitation
- I describe what images would show

#### Degraded Mode
When components fail:
- I continue with available tools
- I explain what's unavailable
- I suggest alternatives

### Session Management

#### New Sessions
Each conversation starts fresh:
- No memory of previous sessions
- New context building
- Re-establishing your interests

#### Session Persistence
Within a session:
- I remember our conversation
- Context carries forward
- Follow-ups work naturally

### Privacy

#### What I Store
- Conversation history (session only)
- Query patterns (anonymous)
- Error logs (for improvement)

#### What I Don't Store
- Personal identifying information
- Session content after session ends
- Data outside the heritage knowledge base

### Getting Help

#### System Status
Check if components are working:
- Use `/health` command
- Check `verify_setup.py`
- Review error messages

#### Common Issues

**No images returned:**
- Vision dependencies not installed
- No images indexed yet
- Query doesn't match image captions

**Text retrieval empty:**
- No documents indexed
- Query outside knowledge base
- Qdrant connection issue

**Slow responses:**
- LLM API latency
- Large result sets
- Complex synthesis required

### Advanced Usage

#### Complex Queries
Combine multiple aspects:
- "Compare Olmec and Maya approaches to [topic]"
- "What do [Source A] and [Source B] say about [topic]?"
- "Show me the archaeological evidence for [claim]"

#### Source Critique
Ask about sources:
- "What are the limitations of these sources?"
- "Are there indigenous perspectives on this?"
- "How recent is this research?"

#### Visual Analysis
When images are available:
- "What can we learn from [Image X]?"
- "Describe the visual features of..."
- "How does this image support the text?"

---

Remember: I'm a tool to help explore cultural heritage, not an authority. Always engage critically with the information I provide.
