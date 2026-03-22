# Reusable AI Skills

Skills are reusable functional units shared across agents. Each skill includes an input/output contract and a list of agents that depend on it.

## recovery_scoring
**Input**
```
{ metrics: HealthMetrics, baselines: Baselines }
```
**Output**
```
{ score: float, status: "green|yellow|red" }
```
**Used by**: HealthAnalysisAgent, TrainingOptimizerAgent

## baseline_delta_calc
**Input**
```
{ metrics: HealthMetrics, baselines: Baselines }
```
**Output**
```
{ hrv_delta: float, sleep_delta: float, rhr_delta: float }
```
**Used by**: HealthAnalysisAgent

## summarize_trends
**Input**
```
{ user_id: string }
```
**Output**
```
{ summary: string, recommendations: string[] }
```
**Used by**: CoachAgent

## anomaly_scan
**Input**
```
{ metrics: HealthMetrics, baselines: Baselines }
```
**Output**
```
{ anomaly: bool, reason: string, severity: "low|med|high" }
```
**Used by**: AnomalyDetectionAgent, CoachAgent

## training_reco
**Input**
```
{ user_id: string, metrics: HealthMetrics }
```
**Output**
```
{ summary: string, recommendations: string[] }
```
**Used by**: TrainingOptimizerAgent

## generate_coaching_summary
**Input**
```
{ metrics: HealthMetrics, recovery: Recovery, baselines: Baselines }
```
**Output**
```
{ summary: string, recommendations: string[], workout_intensity_suggestion: string }
```
**Used by**: CoachAgent

## search_memory
**Input**
```
{ user_id: string, query: string, top_k: int }
```
**Output**
```
MemoryChunk[]
```
**Used by**: All agents (context lookup)

## write_memory
**Input**
```
{ user_id: string, memory_type: string, content: string, metadata: object }
```
**Output**
```
MemoryChunk
```
**Used by**: PlannerAgent, HealthAnalysisAgent
