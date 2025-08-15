# Prompts moved from test_pdf_parser.py to make the agent self-contained
REVIEWER_SYSTEM_PROMPT = """You are a senior AI research expert and technology assessment consultant, specializing in evaluating the potential for scientific research work to be automated by current or near-future AI systems.
Your assessment should be:
1. Systematic and evidence-based using the 12-dimensional framework
2. Objective in analyzing current AI capability boundaries
3. Realistic in predicting technology development trends
4. Comprehensive in considering automation barriers and societal impacts

Maintain critical thinking and provide detailed justifications for each score. Your evaluation will influence research directions and resource allocation decisions."""

EVALUATION_PROMPT_TEMPLATE = """
# Systematic AI Automation Assessment Framework

Please conduct a comprehensive evaluation of the provided academic work using the following 12-dimensional framework. For each dimension, provide detailed analysis and justification for your scoring.

## 12-Dimensional Evaluation Framework

### 1. **Task Formalization** (Score: 0-4)
**What to Evaluate**: Whether the task has clear rules/mathematical objectives
**Score Anchors**: 
- 0: Ill-defined
- 1: Partly formal
- 2: Mostly formal
- 3: Fully formal with minor caveats
- 4: Mathematically exact

**Analysis Required**: Examine the clarity of problem definition, mathematical formulation, and objective functions.

### 2. **Data & Resource Availability** (Score: 0-4)
**What to Evaluate**: Public data, simulators, tool chains availability
**Score Anchors**:
- 0: None
- 1: Sparse/private
- 2: Moderate
- 3: Rich
- 4: Abundant & public

**Analysis Required**: Assess the availability and quality of datasets, existing tools, and computational resources.

### 3. **Input-Output Complexity** (Score: 0-4)
**What to Evaluate**: Modal diversity, structure and length complexity
**Score Anchors**:
- 0: Chaotic
- 1: High complexity
- 2: Moderate complexity
- 3: Low complexity
- 4: Highly regular

**Analysis Required**: Evaluate the complexity of input processing and output generation requirements.

### 4. **Real-World Interaction** (Score: 0-4)
**What to Evaluate**: Need for physical/social/online feedback
**Score Anchors**:
- 0: Constant interaction needed
- 1: Frequent interaction
- 2: Occasional interaction
- 3: Rare interaction
- 4: None (offline)

**Analysis Required**: Determine the extent of real-world interaction and feedback requirements.

### 5. **Existing AI Coverage** (Score: 0-4)
**What to Evaluate**: Proportion of work already completed by existing AI models
**Score Anchors**:
- 0: < 5%
- 1: ≈ 25%
- 2: ≈ 50%
- 3: ≈ 75%
- 4: > 95%

**Analysis Required**: Identify specific existing AI tools/models and quantify coverage percentage.

### 6. **Automation Barriers** (Qualitative Analysis - No Score)
**What to Evaluate**: Major obstacles like creativity, common sense, legal issues
**Analysis Required**: List and explain key barriers preventing full automation:
- Creativity requirements
- Common sense reasoning
- Domain expertise
- Legal/ethical constraints
- Tacit knowledge
- Other specific barriers

### 7. **Human Originality/Irreplaceability** (Score: 0-4)
**What to Evaluate**: Dependence on human creativity and originality
**Score Anchors**:
- 0: Routine work
- 1: Incremental innovation
- 2: Moderately novel
- 3: Clearly novel
- 4: Paradigm-shifting

**Analysis Required**: Assess the level of human creativity, insight, and original thinking required.

### 8. **Safety & Ethical Criticality** (Score: 0-4, Reverse Scoring)
**What to Evaluate**: Consequences of failure/misuse
**Score Anchors**:
- 0: Catastrophic consequences
- 1: Serious consequences
- 2: Manageable consequences
- 3: Minor consequences
- 4: Negligible consequences

**Analysis Required**: Evaluate risks and potential negative impacts of automation.

### 9. **Societal/Economic Impact** (Qualitative Analysis - No Score)
**What to Evaluate**: Net impact after full automation
**Analysis Required**: Describe comprehensive societal and economic implications:
- Job displacement effects
- Research quality changes
- Innovation ecosystem impacts
- Economic benefits/costs
- Social implications

### 10. **Technical Maturity Needed** (Score: 0-4)
**What to Evaluate**: Required R&D depth for automation
**Score Anchors**:
- 0: Multiple breakthroughs needed
- 1: One major breakthrough needed
- 2: Cutting-edge R&D required
- 3: Incremental work needed
- 4: Already solved

**Analysis Required**: Identify specific technical advances needed and their feasibility.

### 11. **3-Year Feasibility** (Probability: 0-100%)
**What to Evaluate**: Probability of AI reaching expert level within 3 years
**Analysis Required**: Provide realistic probability estimate with detailed justification considering:
- Current AI development pace
- Required technical breakthroughs
- Resource availability
- Market incentives

### 12. **Overall Automatability** (Score: 0-4)
**What to Evaluate**: Comprehensive automation feasibility
**Score Anchors**:
- 0: Not automatable
- 1: Hard to automate
- 2: Moderately automatable
- 3: Highly automatable
- 4: Already automatable

**Analysis Required**: Synthesize all dimensions into overall assessment.

## Output Format Requirements

Please structure your response as follows:

# AI Automation Assessment Report

## Executive Summary
[Provide a concise 150-word summary of key findings and overall assessment]

## Detailed Dimensional Analysis

### 1. Task Formalization
**Score: X/4**
[Detailed analysis and justification]

### 2. Data & Resource Availability
**Score: X/4**
[Detailed analysis and justification]

### 3. Input-Output Complexity
**Score: X/4**
[Detailed analysis and justification]

### 4. Real-World Interaction
**Score: X/4**
[Detailed analysis and justification]

### 5. Existing AI Coverage
**Score: X/4**
[Detailed analysis with specific tools/models and coverage percentage]

### 6. Automation Barriers
[Comprehensive list and explanation of key barriers]

### 7. Human Originality/Irreplaceability
**Score: X/4**
[Detailed analysis and justification]

### 8. Safety & Ethical Criticality
**Score: X/4**
[Detailed risk analysis and justification]

### 9. Societal/Economic Impact
[Comprehensive impact analysis]

### 10. Technical Maturity Needed
**Score: X/4**
[Detailed analysis of required advances]

### 11. 3-Year Feasibility
**Probability: X%**
[Detailed probability assessment with reasoning]

### 12. Overall Automatability
**Score: X/4**
[Synthesis of all dimensions with final assessment]

## Summary Scorecard

| Dimension | Score | Key Insight |
|-----------|-------|-------------|
| Task Formalization | X/4 | [Brief insight] |
| Data & Resource Availability | X/4 | [Brief insight] |
| Input-Output Complexity | X/4 | [Brief insight] |
| Real-World Interaction | X/4 | [Brief insight] |
| Existing AI Coverage | X/4 | [Brief insight] |
| Human Originality | X/4 | [Brief insight] |
| Safety & Ethics | X/4 | [Brief insight] |
| Technical Maturity | X/4 | [Brief insight] |
| 3-Year Feasibility | X% | [Brief insight] |
| **Overall Automatability** | **X/4** | **[Key conclusion]** |

## Strategic Recommendations

### For Researchers
[Specific recommendations for researchers in this field]

### For Institutions
[Recommendations for research institutions and funding bodies]

### For AI Development
[Recommendations for AI researchers and developers]

## Assessment Limitations and Uncertainties
[List key limitations, assumptions, and areas of uncertainty in the assessment]

---

**Instructions**: 
- Provide specific evidence and examples for each score
- Be conservative in scoring when uncertain
- Consider both current capabilities and realistic near-term developments
- Justify all numerical scores with detailed reasoning
- For qualitative dimensions, provide comprehensive analysis

Now please begin the systematic evaluation of the provided academic work.
"""

# Tools schema for function calling (Anthropic tools)
# The model must call `return_assessment` to output a strict JSON object
TOOLS = [
    {
        "name": "return_assessment",
        "description": "Return the complete 12D AI automation assessment as a single JSON object.",
        "input_schema": {
            "type": "object",
            "properties": {
                "executive_summary": {"type": "string"},
                "dimensions": {
                    "type": "object",
                    "properties": {
                        "task_formalization": {
                            "type": "object",
                            "properties": {"score": {"type": "number"}, "analysis": {"type": "string"}},
                            "required": ["score", "analysis"],
                        },
                        "data_resource_availability": {
                            "type": "object",
                            "properties": {"score": {"type": "number"}, "analysis": {"type": "string"}},
                            "required": ["score", "analysis"],
                        },
                        "input_output_complexity": {
                            "type": "object",
                            "properties": {"score": {"type": "number"}, "analysis": {"type": "string"}},
                            "required": ["score", "analysis"],
                        },
                        "real_world_interaction": {
                            "type": "object",
                            "properties": {"score": {"type": "number"}, "analysis": {"type": "string"}},
                            "required": ["score", "analysis"],
                        },
                        "existing_ai_coverage": {
                            "type": "object",
                            "properties": {
                                "score": {"type": "number"},
                                "analysis": {"type": "string"},
                                "tools_models": {"type": "array", "items": {"type": "string"}},
                                "coverage_pct_estimate": {"type": "number"},
                            },
                            "required": ["score", "analysis"],
                        },
                        "automation_barriers": {
                            "type": "object",
                            "properties": {"analysis": {"type": "string"}},
                            "required": ["analysis"],
                        },
                        "human_originality": {
                            "type": "object",
                            "properties": {"score": {"type": "number"}, "analysis": {"type": "string"}},
                            "required": ["score", "analysis"],
                        },
                        "safety_ethics": {
                            "type": "object",
                            "properties": {"score": {"type": "number"}, "analysis": {"type": "string"}},
                            "required": ["score", "analysis"],
                        },
                        "societal_economic_impact": {
                            "type": "object",
                            "properties": {"analysis": {"type": "string"}},
                            "required": ["analysis"],
                        },
                        "technical_maturity_needed": {
                            "type": "object",
                            "properties": {"score": {"type": "number"}, "analysis": {"type": "string"}},
                            "required": ["score", "analysis"],
                        },
                        "three_year_feasibility": {
                            "type": "object",
                            "properties": {"probability_pct": {"type": "number"}, "analysis": {"type": "string"}},
                            "required": ["probability_pct", "analysis"],
                        },
                        "overall_automatability": {
                            "type": "object",
                            "properties": {"score": {"type": "number"}, "analysis": {"type": "string"}},
                            "required": ["score", "analysis"],
                        },
                    },
                    "required": [
                        "task_formalization",
                        "data_resource_availability",
                        "input_output_complexity",
                        "real_world_interaction",
                        "existing_ai_coverage",
                        "automation_barriers",
                        "human_originality",
                        "safety_ethics",
                        "societal_economic_impact",
                        "technical_maturity_needed",
                        "three_year_feasibility",
                        "overall_automatability",
                    ],
                },
                "scorecard": {
                    "type": "object",
                    "properties": {
                        "task_formalization": {"type": "number"},
                        "data_resource_availability": {"type": "number"},
                        "input_output_complexity": {"type": "number"},
                        "real_world_interaction": {"type": "number"},
                        "existing_ai_coverage": {"type": "number"},
                        "human_originality": {"type": "number"},
                        "safety_ethics": {"type": "number"},
                        "technical_maturity_needed": {"type": "number"},
                        "three_year_feasibility_pct": {"type": "number"},
                        "overall_automatability": {"type": "number"},
                    },
                    "required": [
                        "task_formalization",
                        "data_resource_availability",
                        "input_output_complexity",
                        "real_world_interaction",
                        "existing_ai_coverage",
                        "human_originality",
                        "safety_ethics",
                        "technical_maturity_needed",
                        "three_year_feasibility_pct",
                        "overall_automatability",
                    ],
                },
                "recommendations": {
                    "type": "object",
                    "properties": {
                        "for_researchers": {"type": "array", "items": {"type": "string"}},
                        "for_institutions": {"type": "array", "items": {"type": "string"}},
                        "for_ai_development": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["for_researchers", "for_institutions", "for_ai_development"],
                },
                "limitations_uncertainties": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "executive_summary",
                "dimensions",
                "scorecard",
                "recommendations",
                "limitations_uncertainties",
            ],
            "additionalProperties": False,
        },
    }
]

TOOL_CHOICE = {"type": "tool", "name": "return_assessment"}