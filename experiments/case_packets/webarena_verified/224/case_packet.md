# Case Packet

## Case Metadata

- domain: `webarena_verified`
- case_unit_id: `224`
- task_id: `224`

## Benchmark Task Summary

- benchmark: `WebArena-Verified v1.2.3 full`
- task type: `RETRIEVE`
- task revision: `2`
- sites: `map`
- official instruction: I am at CMU Pittsburgh, how long does it take to reach the nearest wendys with different transportation methods? Return duration in HH:MM:SS format. (Use the OSRM direction service.)
- official evaluator commit: `6473f72db5dcefc97b5725b59e734504edc28a21`
- evaluator sequence: `AgentResponseEvaluator`
- task score composition: `all evaluator scores must equal 1.0`
- official score field: `TaskEvalResult.score`
- required run artifacts: `agent_response.json`, `network.har`
- maximum browser steps: `30`
- observation/action set: `accessibility_tree` / `id_accessibility_tree`
- reset before each case: `true`

## Visibility Boundary

This canonical source-rich packet is only for checklist drafting and human review.
The tested agent receives only `agent_input.json`; do not place this packet,
`raw_case/`, evaluator expectations, or gold values in the agent prompt.

## Source Inventory

- `derived/task.json`
- `derived/tag_task.json`
- `official/src/webarena_verified/api/internal/evaluator.py`
- `official/src/webarena_verified/core/evaluation/evaluators/base.py`
- `official/src/webarena_verified/core/evaluation/evaluators/agent_response_evaluator.py`
- `official/src/webarena_verified/core/evaluation/value_comparator.py`
- `official/src/webarena_verified/core/evaluation/value_normalizer.py`
- `official/src/webarena_verified/types/agent_response.py`
- `official/src/webarena_verified/types/eval.py`
- `official/src/webarena_verified/types/task.py`

## Packet Source Files

### `derived/task.json`

Source ref: `experiments/official_splits/webarena_verified_official_812.json#task_id=224`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "error_details": null,
        "retrieved_data": [
          "3min"
        ],
        "status": "SUCCESS",
        "task_type": "RETRIEVE"
      },
      "ordered": false,
      "results_schema": {
        "items": {
          "format": "duration",
          "type": "string"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "location": "wendys",
    "retrieved_data_format_spec": "Return duration in HH:MM:SS format"
  },
  "intent": "I am at CMU Pittsburgh, how long does it take to reach the nearest wendys with different transportation methods? Return duration in HH:MM:SS format. (Use the OSRM direction service.)",
  "intent_template": "I am at CMU Pittsburgh, how long does it take to reach the nearest {{location}} with different transportation methods? {{retrieved_data_format_spec}}. (Use the OSRM direction service.)",
  "intent_template_id": 35,
  "revision": 2,
  "sites": [
    "map"
  ],
  "start_urls": [
    "__MAP__"
  ],
  "task_id": 224
}
```

### `derived/tag_task.json`

Source ref: `experiments/official_splits/webarena_verified_v1_2_3_source/assets/dataset/webarena-verified.json#task_id=224`

```json
{
  "eval": [
    {
      "evaluator": "AgentResponseEvaluator",
      "expected": {
        "retrieved_data": [
          "3min"
        ],
        "status": "SUCCESS",
        "task_type": "retrieve"
      },
      "results_schema": {
        "items": {
          "format": "duration",
          "type": "string"
        },
        "type": "array"
      }
    }
  ],
  "instantiation_dict": {
    "location": "wendys",
    "retrieved_data_format_spec": "Return duration in HH:MM:SS format"
  },
  "intent": "I am at CMU Pittsburgh, how long does it take to reach the nearest wendys with different transportation methods? Return duration in HH:MM:SS format. (Use the OSRM direction service.)",
  "intent_template": "I am at CMU Pittsburgh, how long does it take to reach the nearest {{location}} with different transportation methods? {{retrieved_data_format_spec}}. (Use the OSRM direction service.)",
  "intent_template_id": 35,
  "revision": 2,
  "sites": [
    "map"
  ],
  "start_urls": [
    "__MAP__"
  ],
  "task_id": 224
}
```

### `official/src/webarena_verified/api/internal/evaluator.py`

Source ref: `https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/api/internal/evaluator.py`

```python
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from webarena_verified.core.evaluation.evaluators import EVALUATOR_REGISTRY
from webarena_verified.core.utils import logger
from webarena_verified.core.utils.checksum import compute_data_file_checksum
from webarena_verified.types.config import EnvironmentConfig, WebArenaVerifiedConfig
from webarena_verified.types.eval import EvaluatorResult, TaskEvalContext, TaskEvalResult, TransformedAgentResponse
from webarena_verified.types.task import WebArenaSite
from webarena_verified.types.tracing import NetworkTrace

from .data_reader import WebArenaVerifiedDataReader


class WebArenaVerifiedEvaluator:
    """Programmatic interface for evaluating WebArena tasks.

    Simplified API: Evaluate tasks by providing TaskEvalContext directly.
    """

    def __init__(self, *, config: WebArenaVerifiedConfig, reader: WebArenaVerifiedDataReader) -> None:
        self.config = config
        self.reader = reader

    def evaluate_task(
        self,
        *,
        context: TaskEvalContext | None = None,
        task_id: int | None = None,
        agent_response: Any = None,
        network_trace: Any = None,
    ) -> TaskEvalResult:
        """Evaluate a single task with automatic format detection.

        This method supports two calling patterns:
        1. With context: evaluate_task(context=TaskEvalContext(...))
        2. With individual parameters: evaluate_task(task_id=1, agent_response=..., network_trace=...)

        Args:
            context: Pre-built TaskEvalContext (mutually exclusive with task_id/agent_response/network_trace)
            task_id: ID of the task to evaluate (required if context is None)
            agent_response: Agent's response in any of these formats:
                - str: Raw response text (e.g., "answer: 42" or "navigate: https://example.com")
                - dict: Parsed response dict (e.g., {"action": "retrieve", "value": "42"})
                - list: List of values (may result in validation failure)
                - None: No response (may result in validation failure)
                - Path: File path to read response from
            network_trace: Network trace in any of these formats:
                - Path: HAR file path
                - list: Pre-parsed list of network events/requests
                - NetworkTrace: Pre-constructed NetworkTrace object

        Returns:
            TaskEvalResult with status, score, and detailed evaluation results.
            Errors are captured in result.status = EvalStatus.ERROR with result.error_msg.

        Raises:
            ValueError: If both calling patterns are used or neither is used

        Examples:
            Using context (backward compatible):
            >>> context = TaskEvalContext(...)
            >>> result = evaluator.evaluate_task(context=context)

            Using individual parameters:
            >>> result = evaluator.evaluate_task(
            ...     task_id=1,
            ...     agent_response="answer: 42",
            ...     network_trace=Path("trace.har")
            ... )
        """
        has_context = context is not None
        has_individual_params = task_id is not None

        if has_context and has_individual_params:
            raise ValueError(
                "Cannot provide both 'context' and individual parameters "
                "(task_id, agent_response, network_trace). Use one calling pattern only."
            )

        if not has_context and not has_individual_params:
            raise ValueError("Must provide either 'context' or task_id (with agent_response and network_trace).")

        if has_context:
            assert context is not None
            return self._evaluate_with_context(context=context)

        assert task_id is not None, "task_id must be provided when using individual parameters"

        logger.info(f"Evaluating task {task_id}")
        try:
            task = self.reader.get_task_by_id(task_id)

            agent_response_raw = self._parse_agent_response(agent_response)
            network_trace_obj = self._parse_network_trace(network_trace)

            eval_context = TaskEvalContext(
                task=task,
                agent_response_raw=agent_response_raw,
                network_trace=network_trace_obj,
                config=self.config,
            )

            return self._evaluate_with_context(context=eval_context)

        except Exception as e:
            error_msg = f"Failed to evaluate task {task_id}: {e}"
            logger.error(error_msg, exc_info=True)
            return self._create_eval_error_result(task_id, error_msg)

    def _evaluate_with_context(self, *, context: TaskEvalContext) -> TaskEvalResult:
        """Evaluate a single task.

        Args:
            context: TaskEvalContext with task definition, agent response, network trace, and URL map

        Returns:
            TaskEvalResult with evaluation score, status, and detailed assertions

        Examples:
            >>> evaluator = WebArenaVerifiedEvaluator(config=config, reader=reader)
            >>> task = reader.get_task_by_id(1)
            >>> context = TaskEvalContext(
            ...     task=task,
            ...     agent_response_raw=agent_response_json,
            ...     network_trace=NetworkTrace.from_content(trace_file),
            ...     url_map=config.url_map
            ... )
            >>> result = evaluator.evaluate_task(context=context)
            >>> print(f"Score: {result.score}, Status: {result.status}")
        """

        validated_config = self._validate_config_for_eval(context=context)
        context = context.model_copy(update={"config": validated_config})

        task_id = context.task.task_id
        intent_template_id = context.task.intent_template_id
        sites = context.task.sites
        revision = context.task.revision

        logger.info(f"Starting evaluation for task_id={task_id}, intent_template_id={intent_template_id}")
        evaluators_results: list[EvaluatorResult] = []
        data_checksum = compute_data_file_checksum(self.config.test_data_file)

        try:
            for eval_cfg in context.task.eval:
                evaluator_class = EVALUATOR_REGISTRY.get(eval_cfg.evaluator)
                if evaluator_class is None:
                    raise KeyError(
                        f"Evaluator '{eval_cfg.evaluator}' not found. "
                        f"Available evaluators: {list(EVALUATOR_REGISTRY.keys())}"
                    )
                evaluator = evaluator_class()
                evaluator_result = evaluator.evaluate(context=context, config=eval_cfg)
                evaluators_results.append(evaluator_result)

            assert len(context.task.eval) == len(evaluators_results), (
                f"Number of evaluator results ({len(evaluators_results)}) does not match number of evaluators "
                f"in task config ({len(context.task.eval)}) for task {task_id}"
            )
            return TaskEvalResult.create(
                task_id=task_id,
                intent_template_id=intent_template_id,
                sites=sites,
                task_revision=revision,
                evaluators_results=evaluators_results,
                data_checksum=data_checksum,
            )

        except Exception as e:
            error_msg = f"Error during evaluation orchestration for task {task_id}: {e}"
            logger.error(error_msg, exc_info=True)
            return TaskEvalResult.create(
                task_id=task_id,
                intent_template_id=intent_template_id,
                sites=sites,
                task_revision=revision,
                data_checksum=data_checksum,
                error_msg=error_msg,
                is_error=True,
                evaluators_results=evaluators_results,
            )

    def _parse_agent_response(self, agent_response: Any) -> Any:
        """Parse agent response to the format expected by evaluators.

        Args:
            agent_response: Response in str, dict, list, None, or Path format

        Returns:
            Raw agent response (str, dict, list, or None) ready for evaluation

        Raises:
            TypeError: If agent_response type is not supported
            FileNotFoundError: If Path does not exist
            ValueError: If file content is invalid
        """
        if isinstance(agent_response, (str, dict, list, type(None), TransformedAgentResponse)):
            return agent_response
        if isinstance(agent_response, Path):
            logger.info(f"Loading agent response from file: {agent_response}")
            if not agent_response.exists():
                raise FileNotFoundError(f"Agent response file not found: {agent_response}")

            return agent_response.read_text()
        raise TypeError(f"agent_response must be str, dict, list, None, or Path, got {type(agent_response)}")

    def _parse_network_trace(self, network_trace: Any) -> NetworkTrace:
        """Parse network trace to NetworkTrace object.

        Args:
            network_trace: Trace in list, Path, or NetworkTrace format

        Returns:
            NetworkTrace object ready for evaluation

        Raises:
            TypeError: If network_trace type is not supported
            FileNotFoundError: If Path does not exist
            ValueError: If content is invalid HAR format
        """
        if isinstance(network_trace, NetworkTrace) or network_trace is None:
            return network_trace

        if isinstance(network_trace, Path):
            logger.info(f"Loading network trace from file: {network_trace}")
            if not network_trace.exists():
                raise FileNotFoundError(f"Network trace file not found: {network_trace}")
            return NetworkTrace.from_content(network_trace)

        if isinstance(network_trace, (list, tuple)):
            return NetworkTrace.from_content(list(network_trace) if isinstance(network_trace, tuple) else network_trace)

        raise TypeError(f"network_trace must be list, Path, or NetworkTrace, got {type(network_trace)}")

    def _create_eval_error_result(self, task_id: int, error_msg: str) -> TaskEvalResult:
        """Create an error result for unhandled evaluation errors.

        Args:
            task_id: Task ID that failed
            error_msg: Error message describing the failure

        Returns:
            TaskEvalResult with ERROR status and error message
        """
        try:
            task = self.reader.get_task_by_id(task_id)
            intent_template_id = task.intent_template_id
            sites = task.sites
            revision = task.revision
        except Exception:
            intent_template_id = -1
            sites = ()
            revision = -1

        try:
            data_checksum = compute_data_file_checksum(self.config.test_data_file)
        except Exception:
            data_checksum = "error"

        return TaskEvalResult.create(
            task_id=task_id,
            intent_template_id=intent_template_id,
            sites=sites,
            task_revision=revision,
            data_checksum=data_checksum,
            error_msg=error_msg,
            is_error=True,
        )

    def _validate_config_for_eval(self, *, context: TaskEvalContext) -> WebArenaVerifiedConfig | None:
        """Try to correct eval config by extracting URL from network trace as fallback.

        If config.environments is None, this function attempts to extract the base URL
        from the first network event in the trace and create a minimal EnvironmentConfig.

        Args:
            context: TaskEvalContext with network trace and task information

        Returns:
            Updated config with environments populated from network trace, or original config if:
            - config.environments already exists
            - network_trace is None
            - network_trace has no events
            - URL extraction fails

        Note:
            This is a fallback mechanism for cases where config doesn't include environments.
            It creates a minimal EnvironmentConfig using the base URL from the first network event.
        """

        is_valid_config = True
        if context.config.environments:
            is_valid_config = all(
                site in context.config.environments and context.config.environments[site].urls
                for site in context.task.sites
            )
        else:
            is_valid_config = False

        if is_valid_config:
            return context.config

        logger.info("Attempting to correct eval config from network trace if needed due to empty environment urls")

        # Can't extract URL without trace
        if context.network_trace is None or not context.network_trace.evaluation_events:
            raise ValueError("Invalid config: environments missing and network trace unavailable")

        try:
            # Best effort: extract base URL from a network event per site
            environments = {}
            for idx, site in enumerate(context.task.sites):
                # Use event at index if available, otherwise fall back to first event
                event_idx = min(idx, len(context.network_trace.evaluation_events) - 1)
                first_event = context.network_trace.evaluation_events[event_idx]
                first_url = first_event.url
                parsed_url = urlparse(first_url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                logger.info(f"Config auto correct using base URL from network trace: {base_url}")

                # For admin sites, append /admin path
                if site == WebArenaSite.SHOPPING_ADMIN:
                    site_url = f"{base_url}/admin"
                else:
                    site_url = base_url

                environments[site] = EnvironmentConfig(urls=[site_url])

            # Create new config with corrected environments
            corrected_config = context.config.model_copy(deep=True)
            corrected_config.environments = environments

            logger.warning(
                f"Auto-corrected config using best-effort URL extraction from trace "
                f"for sites: {[s.name for s in context.task.sites]}. "
                "This is not recommended - please provide a proper config with environment URLs."
            )
            return corrected_config

        except Exception as e:
            raise ValueError(f"Failed to correct eval config from network trace: {e}") from e
```

### `official/src/webarena_verified/core/evaluation/evaluators/base.py`

Source ref: `https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/core/evaluation/evaluators/base.py`

```python
from abc import ABC, abstractmethod
from types import MappingProxyType
from typing import Any, Generic, TypeVar

from webarena_verified.core.evaluation.data_types import NormalizedType
from webarena_verified.core.evaluation.value_comparator import ValueComparator
from webarena_verified.core.evaluation.value_normalizer import ValueNormalizer
from webarena_verified.core.utils import logger
from webarena_verified.types.eval import EvalAssertion, EvaluatorResult, TaskEvalContext
from webarena_verified.types.task import BaseEval

EvalConfigT = TypeVar("EvalConfigT", bound=BaseEval[Any])


class BaseEvaluator(ABC, Generic[EvalConfigT]):
    """Abstract base class for task evaluators."""

    def __init__(self) -> None:
        self.value_comparator = ValueComparator()
        self.value_normalizer = ValueNormalizer()

    @property
    def name(self) -> str:
        """Return evaluator class name."""
        return self.__class__.__name__

    def evaluate(self, *, context: TaskEvalContext, config: EvalConfigT) -> EvaluatorResult:
        """Main evaluation flow using four-step process.

        Steps:
        1. Get actual value (evaluator-specific extraction)
        2. Get expected value (from config)
        3. Normalize both values (using ValueNormalizer)
        4. Compare normalized values (using ValueComparator)

        Args:
            context: Task evaluation context
            config: Evaluator configuration

        Returns:
            EvaluatorResult with assertions and normalized values
        """
        # Sanity check
        assert self.name == config.evaluator, f"Evaluator name mismatch: {self.name} != {config.evaluator}"  # type: ignore

        # TODO: Rename config to eval_cfg for clarity
        assertions = None
        error_occurred = False
        error_msg = None
        actual_raw = None
        expected_raw = None
        actual_normalized = None
        expected_normalized = None

        try:
            # Step 1: Get actual value (evaluator-specific)
            actual_raw = self._get_actual_value(context, config)

            # Step 2: Get expected value (from task expected data in config)
            expected_raw = self._get_expected_value(config)

            # Step 3: Normalize both values
            expected_normalized = self._normalized_expected_value(
                expected_raw,
                config=config,
                context=context,
            )
            actual_normalized = self._normalized_actual_value(
                actual_raw,
                expected_normalized,
                config=config,
                context=context,
            )

            # Step 4: Compare normalized values
            assertions = self._compare_values(
                actual_normalized=actual_normalized,
                expected_normalized=expected_normalized,
                config=config,
                context=context,
                ordered=False,
            )

        except Exception as e:
            error_msg = f"Error during evaluation with evaluator {self.name} for task {context.task.task_id}: {e}"
            logger.exception(error_msg)
            error_occurred = True

        return EvaluatorResult.create(
            evaluator_name=self.name,
            assertions=assertions,
            is_error=error_occurred,
            error_msg=error_msg,
            actual=actual_raw,
            actual_normalized=self._parse_normalized_value_for_reporting(actual_normalized),
            expected=self._parse_normalized_value_for_reporting(expected_normalized),
            should_not_exist=getattr(config, "should_not_exist", None),
        )

    # ========================================================================
    # Abstract Methods (Must be implemented by subclasses)
    # ========================================================================

    @abstractmethod
    def _get_actual_value(self, context: TaskEvalContext, config: EvalConfigT) -> Any:
        """Extract and navigate to the actual value from evaluation context.

        **Step 1: Get Actual Value**

        Purpose: Extract raw value from context before normalization.

        Evaluator-Specific Implementation:
        - AgentResponseEvaluator: Extract from context.agent_response
        - NetworkEventEvaluator: Extract from context.network_trace.events

        May include navigation to specific field using value_path:
        - Example: 'retrieved_data' from agent response
        - Example: 'headers.referer' from network event

        Args:
            context: Task evaluation context
            config: Evaluator configuration

        Returns:
            Raw value (before normalization) which can be:
            - Simple value (string, number, boolean)
            - Array of simple values
            - Object (dictionary)
            - Array of objects

        Note:
            This is the ONLY step that is evaluator-specific. All other steps
            (get expected, normalize, compare) use the same logic across evaluators.
        """

    @abstractmethod
    def _normalized_expected_value(self, expected_raw: Any, config: EvalConfigT, context: TaskEvalContext) -> Any:
        """Normalize expected value.

        **Step 3a: Normalize Expected Value**

        Purpose: Convert expected value to normalized form for comparison.

        Args:
            expected_raw: Raw expected value from config
            config: Evaluator configuration
            context: Task evaluation context

        Returns:
            Normalized value (NormalizedType, list, or dict)
        """
        ...

    @abstractmethod
    def _normalized_actual_value(
        self, actual_raw: Any, normalized_expected: Any, config: EvalConfigT, context: TaskEvalContext
    ) -> Any:
        """Normalize actual value.

        **Step 3b: Normalize Actual Value**

        Purpose: Convert actual value to normalized form for comparison.

        Args:
            actual_raw: Raw actual value from context
            normalized_expected: Already normalized expected value (for context)
            config: Evaluator configuration
            context: Task evaluation context

        Returns:
            Normalized value (NormalizedType, list, or dict)
        """
        ...

    @abstractmethod
    def _compare_values(
        self,
        *,
        actual_normalized: NormalizedType | list[NormalizedType] | dict | MappingProxyType | None,
        expected_normalized: NormalizedType | list[NormalizedType] | dict | MappingProxyType | None,
        config: EvalConfigT,
        context: TaskEvalContext,
        ordered: bool = False,
    ) -> list[EvalAssertion]:
        """Compare normalized actual vs expected values.

        Must be implemented by subclasses to provide context-aware comparison logic.

        Args:
            actual_normalized: Normalized actual value (can be None)
            expected_normalized: Normalized expected value (can be None)
            config: Evaluator configuration (required for subclass-specific logic)
            context: Task evaluation context (required for context-aware comparison)
            ordered: Whether array order matters for comparison

        Returns:
            List of EvalAssertion objects (empty list = success)
        """
        ...

    # ========================================================================
    # Helper Methods (Can be overridden by subclasses)
    # ========================================================================

    def _get_expected_value(self, config: EvalConfigT) -> Any:
        """Get expected value from evaluator configuration.

        **Step 2: Get Expected Value**

        Purpose: Extract expected value(s) from config.expected field.

        Source: Always comes from config.expected

        Supports Alternatives at Individual Value Level:
        - Single value: "success"
        - Single value with alternatives: ["success", "ok", "completed"]
        - Array with element-level alternatives: [[10, 17], 15]
        - Object with property-level alternatives: {"status": ["success", "ok"], "code": 200}

        Key Pattern: When a value is a list, it means "any of these alternatives is valid"
        - At root level: ["success", "ok"] → single value with alternatives
        - In array: [[10, 17], 15] → first element has alternatives
        - In object: {status: ["success", "ok"]} → property has alternatives

        Args:
            config: Evaluator configuration

        Returns:
            Raw expected value(s) (before normalization)

        Note:
            This method can be overridden by subclasses if they need custom
            logic for extracting expected values from config.
        """
        return config.expected

    def _parse_normalized_value_for_reporting(self, value: Any) -> Any:
        if isinstance(value, NormalizedType):
            return value.normalized
        if isinstance(value, (list, tuple)):
            return [self._parse_normalized_value_for_reporting(v) for v in value]
        if isinstance(value, dict):
            return {k: self._parse_normalized_value_for_reporting(v) for k, v in value.items()}

        return value
```

### `official/src/webarena_verified/core/evaluation/evaluators/agent_response_evaluator.py`

Source ref: `https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/core/evaluation/evaluators/agent_response_evaluator.py`

```python
import json
import logging
import re
from contextlib import suppress
from functools import partial
from types import MappingProxyType
from typing import Any

from webarena_verified.core.evaluation.data_types import NormalizedString
from webarena_verified.types.agent_response import _FinalAgentResponse
from webarena_verified.types.eval import (
    EvalAssertion,
    EvalStatus,
    TaskEvalContext,
    TransformedAgentResponse,
)
from webarena_verified.types.task import AgentResponseEvaluatorCfg

from .base import BaseEvaluator

logger = logging.getLogger(__name__)


class AgentResponseEvaluator(BaseEvaluator[AgentResponseEvaluatorCfg]):
    """Evaluator for agent responses using four-step architecture.

    Validates the agent's response structure, task type, status,
    and retrieved data against expected values with alternatives support.

    Architecture:
    - Step 1: Extract agent response from context (parse JSON, validate format)
    - Step 2: Get expected response from config (with alternatives)
    - Step 3: Normalize both using schema-based normalization
    - Step 4: Compare normalized values structurally
    """

    def _get_actual_value(self, context: TaskEvalContext, config: AgentResponseEvaluatorCfg) -> Any:
        return context.agent_response_raw

    def _get_expected_value(self, config: AgentResponseEvaluatorCfg) -> Any:
        """Get expected value from config.

        Returns:
            Expected agent response as dict with alternatives support
        """
        return config.expected

    def _normalized_expected_value(
        self, expected_raw: _FinalAgentResponse, config: AgentResponseEvaluatorCfg, context: TaskEvalContext
    ) -> MappingProxyType:
        if not isinstance(expected_raw, _FinalAgentResponse):
            raise TypeError(f"Expected value must be of type _FinalAgentResponse, got {type(expected_raw).__name__}")
        normalized_retrieved_data = self._normalized_retrieved_data(
            retrieved_data_raw=expected_raw.retrieved_data,
            strict=True,
            context=context,
            config=config,
        )
        return MappingProxyType(
            {
                "task_type": NormalizedString(expected_raw.task_type),
                "status": NormalizedString(expected_raw.status),
                "retrieved_data": normalized_retrieved_data,
            }
        )

    def _get_actual_agent_response_dict(self, actual_raw: Any) -> Any:
        value = actual_raw
        if isinstance(value, str):
            value = value.strip()

        if isinstance(actual_raw, TransformedAgentResponse):
            value = actual_raw.transformed_response
        elif isinstance(actual_raw, str):
            # Extract JSON from code blocks (```json ... ``` or ``` ... ```)
            code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
            match = re.search(code_block_pattern, actual_raw, re.DOTALL)
            if match:
                value = match.group(1).strip()

            with suppress(json.JSONDecodeError):
                value = json.loads(value)

        return value or None

    def _normalized_actual_value(
        self, actual_raw: Any, normalized_expected: Any, config: AgentResponseEvaluatorCfg, context: TaskEvalContext
    ) -> Any:
        value = self._get_actual_agent_response_dict(actual_raw=actual_raw)
        if not isinstance(value, (dict, MappingProxyType)):
            return value

        _normalized_values = {}
        for k in config.expected.model_fields_set:
            if k == "task_type" and k not in value and "performed_operation" in value:
                k = "performed_operation"  # Support legacy field name

            if k not in value:
                if k == "retrieved_data":
                    # When retrieved_data key is missing, treat it as None for comparison
                    # This allows missing key to match expected None (e.g., NOT_FOUND_ERROR tasks)
                    _normalized_values[k] = None
                continue

            if k == "retrieved_data":
                _attr_value = value.get(k, "")
                _normalized_value = (
                    self._normalized_retrieved_data(
                        retrieved_data_raw=_attr_value,
                        strict=False,
                        context=context,
                        config=config,
                    )
                    if context.task.is_retrieve_task
                    else None
                )
            else:
                _normalized_value = None
                # All other fields are normalized as NormalizedString
                if _attr_value := value.get(k, "").strip():
                    _normalized_value = _attr_value
                    with suppress(ValueError):
                        _normalized_value = NormalizedString(_attr_value)

                if k == "performed_operation":
                    k = "task_type"  # Store under new field name

            if k in _normalized_values:
                raise ValueError(f"Duplicate key '{k}' found during normalization.")

            _normalized_values[k] = _normalized_value or None

        return MappingProxyType(_normalized_values)

    def _normalized_retrieved_data(
        self, *, retrieved_data_raw: Any, strict: bool, context: TaskEvalContext, config: AgentResponseEvaluatorCfg
    ) -> Any:
        if not retrieved_data_raw and not isinstance(retrieved_data_raw, (int, float, bool)):
            # None and empty cases
            return None

        retrieved_data_raw = (
            (retrieved_data_raw,) if not isinstance(retrieved_data_raw, (list, tuple)) else tuple(retrieved_data_raw)
        )
        _derender_url_fct = partial(context.config.derender_url, sites=context.task.sites, strict=strict)
        # TODO: Maybe call normalize array directly here
        return self.value_normalizer.normalize_array(
            retrieved_data_raw,
            config.results_schema,
            strict=strict,
            derender_url_fct=_derender_url_fct,
        )

    def _compare_values(  # type: ignore[override]
        self,
        *,
        actual_normalized: Any,
        expected_normalized: MappingProxyType,
        config: AgentResponseEvaluatorCfg,
        context: TaskEvalContext,
        **kwargs: Any,
    ) -> list[EvalAssertion]:
        """Compare normalized actual vs expected using ValueComparator."""
        # Compare all keys except the value of retrieved_data
        assertions = []

        assertions.extend(
            self.value_comparator.compare(
                expected=expected_normalized,
                actual=actual_normalized,
                ignored_values_keys={"retrieved_data"},
                value_name="agent_response",
            )
        )

        if not isinstance(actual_normalized, (dict, MappingProxyType)):
            return assertions

        # Compare retrieved_data
        actual_retrieved_data = actual_normalized.get("retrieved_data", None)
        if not context.task.is_retrieve_task or not actual_normalized:
            # Ignore retrieved_data comparison for non-retrieve tasks or invalid actual response
            return assertions

        expected_retrieved_data = expected_normalized.get("retrieved_data", None)

        if expected_retrieved_data is None and actual_retrieved_data is None:
            # Both None - success, no data expected and none provided
            return assertions

        if expected_retrieved_data is None and actual_retrieved_data is not None:
            # Expected None but got data - failure
            assertions.append(
                EvalAssertion.create(
                    assertion_name="retrieved_data_unexpected",
                    status=EvalStatus.FAILURE,
                    assertion_msgs=[f"Expected no retrieved_data, but got {actual_retrieved_data}"],
                )
            )
            return assertions

        if actual_retrieved_data is None:
            # Expected data but got None - failure
            assertions.append(
                EvalAssertion.create(
                    assertion_name="retrieved_data_missing_or_null",
                    status=EvalStatus.FAILURE,
                    assertion_msgs=[f"Expected retrieved_data to be {expected_retrieved_data}, but got None or empty"],
                )
            )
            return assertions

        # Both have data - compare them
        assertions.extend(
            self.value_comparator.compare(
                expected=tuple(expected_retrieved_data),
                actual=tuple(actual_retrieved_data),
                value_name="retrieved_data",
                ordered=config.ordered,
            )
        )

        return assertions
```

### `official/src/webarena_verified/core/evaluation/value_comparator.py`

Source ref: `https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/core/evaluation/value_comparator.py`

```python
"""Value comparison with recursive structural matching.

This comparator performs recursive structural comparison for nested objects and arrays,
delegating value comparison to NormalizedType.__eq__. Alternatives are handled internally
by NormalizedType instances.
"""

from types import MappingProxyType
from typing import Any

from webarena_verified.core.evaluation.data_types import NormalizedType
from webarena_verified.types.eval import EvalAssertion, EvalStatus


class ValueComparator:
    """Compares normalized values using recursive structural matching.

    Performs recursive comparison for nested structures (arrays, objects) and delegates
    value equality to NormalizedType.__eq__ for handling alternatives. Includes circular
    reference detection to prevent infinite recursion.

    Responsibilities:
    - Recursive structural comparison (arrays, objects, nested structures)
    - Circular reference detection and prevention
    - Clear error messages with full path information

    NOT responsible for:
    - Alternative handling (done by NormalizedType.__eq__)
    - Value normalization (done by ValueNormalizer)

    Example:
        comparator = ValueComparator()

        # Single value with alternatives
        expected = NormalizedString(['success', 'ok'])
        actual = NormalizedString('success')
        comparator.compare(actual, expected)
        # → [] (success)

        # Nested structures
        expected = {'status': NormalizedString('ok'), 'items': [Number(1), Number(2)]}
        actual = {'status': NormalizedString('ok'), 'items': [Number(1), Number(2)]}
        comparator.compare(actual, expected)
        # → [] (success)
    """

    def compare(
        self,
        actual: Any,
        expected: Any,
        ordered: bool = False,
        value_name: str = "value",
        ignored_values_keys: set | None = None,
        ignore_extra_keys: bool = False,
    ) -> list[EvalAssertion]:
        """Compare actual against expected values recursively.

        Args:
            actual: Actual value (primitives, NormalizedType, list, tuple, dict, MappingProxyType)
            expected: Expected value (may contain alternatives via NormalizedType)
            ordered: Whether order matters for array comparisons
            value_name: Root name for error paths (default: "value")
            ignored_values_keys: Object keys to ignore during comparison
            ignore_extra_keys: Whether to allow extra keys in actual objects

        Returns:
            List of EvalAssertion (empty = success, non-empty = failure)

        Raises:
            ValueError: If circular reference detected in actual value
        """
        # Initialize visited tracking for circular reference detection
        visited: set[int] = set()

        return self._compare_recursive(
            actual=actual,
            expected=expected,
            ordered=ordered,
            path=value_name,
            ignored_values_keys=ignored_values_keys,
            ignore_extra_keys=ignore_extra_keys,
            visited=visited,
        )

    def _compare_arrays(
        self,
        *,
        expected_array: list | tuple,
        actual_array: Any,
        value_name: str,
        ordered: bool = False,
        visited: set[int] | None = None,
        **kwargs: Any,
    ) -> list[EvalAssertion]:
        """Dispatch array comparison to ordered or unordered method.

        Args:
            expected_array: Expected array
            actual_array: Actual value (validated to be array)
            value_name: Path name for error messages
            ordered: Whether to use ordered comparison
            visited: Set of visited object IDs for circular reference detection

        Returns:
            List of EvalAssertion (empty if match)
        """
        if not isinstance(expected_array, (list, tuple)):
            raise TypeError(f"Expected array must be list or tuple, got {type(expected_array).__name__}")

        if not isinstance(actual_array, (list, tuple)):
            return [
                EvalAssertion.create(
                    assertion_name=f"{value_name}_invalid_format",
                    status=EvalStatus.FAILURE,
                    assertion_msgs=[f"Expected an array, but got: {type(actual_array).__name__}"],
                )
            ]

        if ordered:
            return self._compare_arrays_ordered(
                expected_array, actual_array, value_name, ordered, visited=visited, **kwargs
            )
        return self._compare_arrays_unordered(
            expected_array, actual_array, value_name, ordered, visited=visited, **kwargs
        )

    def _compare_arrays_unordered(
        self,
        expected_array: list | tuple,
        actual_array: list | tuple,
        value_name: str,
        ordered: bool,
        visited: set[int] | None = None,
        **kwargs: Any,
    ) -> list[EvalAssertion]:
        """Compare arrays ignoring order using greedy matching.

        For each expected element, finds first unmatched actual element that equals it.
        Handles duplicates correctly (e.g., expected=[X, X] requires actual to have 2+ copies of X).
        Uses trial visited sets to avoid false circular reference detection during matching.

        Args:
            expected_array: Expected array
            actual_array: Actual array
            value_name: Path name for error messages
            ordered: Whether nested sequences are order-sensitive
            visited: Set of visited object IDs for circular reference detection

        Returns:
            List of EvalAssertion (empty if match)
        """
        assertions = []

        # Track which actual elements have been matched
        actual_matched = [False] * len(actual_array)

        # Track expected elements that couldn't be matched
        unmatched_expected_indices = []

        # For each expected element, try to find a matching actual element
        for exp_idx, expected_val in enumerate(expected_array):
            matched = False

            # Find first unmatched actual element that equals this expected element
            for act_idx, actual_val in enumerate(actual_array):
                if not actual_matched[act_idx]:
                    # Use recursive comparison for nested structures
                    # Copy visited set for trial comparisons in unordered matching
                    # This prevents false circular reference detection when trying
                    # the same actual item against multiple expected items
                    trial_visited = visited.copy() if visited else set()
                    nested_assertions = self._compare_recursive(
                        actual=actual_val,
                        expected=expected_val,
                        ordered=ordered,
                        path=f"{value_name}[{exp_idx}]",
                        visited=trial_visited,
                        **kwargs,
                    )
                    if not nested_assertions:  # Empty list means match
                        # Found a match - update the main visited set with the trial results
                        if visited is not None:
                            visited.update(trial_visited)
                        actual_matched[act_idx] = True
                        matched = True
                        break

            if not matched:
                unmatched_expected_indices.append(exp_idx)

        # Find extra actual elements (those that weren't matched)
        extra_actual_indices = [i for i, matched in enumerate(actual_matched) if not matched]

        # Generate assertion for mismatches
        if unmatched_expected_indices or extra_actual_indices:
            # Calculate how many expected elements were successfully matched
            matched_count = len(expected_array) - len(unmatched_expected_indices)
            total_expected = len(expected_array)
            num_missing = len(unmatched_expected_indices)
            num_extra = len(extra_actual_indices)

            # Format arrays for display
            expected_display = self._format_array_for_display(expected_array)
            actual_display = self._format_array_for_display(actual_array)

            # Create contextual message based on failure type
            if num_missing == 0 and num_extra > 0:
                # All expected found, but extras present
                message = (
                    f"Array contains all expected elements ({matched_count}/{total_expected}) "
                    f"but has {num_extra} extra element(s)"
                )
            elif num_missing > 0 and num_extra == 0:
                # Some expected missing, no extras
                message = (
                    f"Array is missing {num_missing} expected element(s). Matched ({matched_count}/{total_expected})"
                )
            else:
                # Both missing and extras
                message = (
                    f"Array value mismatch (unordered). "
                    f"Matched ({matched_count}/{total_expected}), Missing: {num_missing}, Extra: {num_extra}"
                )

            assertions.append(
                EvalAssertion.create(
                    assertion_name=f"{value_name}_array_values_mismatch",
                    status=EvalStatus.FAILURE,
                    assertion_msgs=[
                        message,
                        f"Expected: {expected_display}, Got: {actual_display}",
                    ],
                )
            )

        return assertions

    def _compare_arrays_ordered(
        self,
        expected_array: list | tuple,
        actual_array: list | tuple,
        value_name: str,
        ordered: bool,
        visited: set[int] | None = None,
        **kwargs: Any,
    ) -> list[EvalAssertion]:
        """Compare arrays element-by-element in order.

        Compares arrays positionally: expected[i] must match actual[i].
        Reports length mismatches and value mismatches at specific indices.

        Args:
            expected_array: Expected array
            actual_array: Actual array
            value_name: Path name for error messages
            ordered: Whether nested sequences are order-sensitive
            visited: Set of visited object IDs for circular reference detection

        Returns:
            List of EvalAssertion (empty if match)
        """
        assertions = []

        # Compare element-by-element
        min_length = min(len(expected_array), len(actual_array))
        mismatched_indices = []

        for i in range(min_length):
            expected_val = expected_array[i]
            actual_val = actual_array[i]

            # Use recursive comparison for nested structures
            nested_assertions = self._compare_recursive(
                actual=actual_val,
                expected=expected_val,
                ordered=ordered,
                path=f"{value_name}[{i}]",
                visited=visited,
                **kwargs,
            )
            if nested_assertions:  # Non-empty list means mismatch
                mismatched_indices.append(i)
                # Accumulate nested assertions
                assertions.extend(nested_assertions)

        # Check for length mismatch and add missing/extra indices
        if len(expected_array) != len(actual_array):
            if len(actual_array) < len(expected_array):
                # Missing elements at the end
                missing_indices = list(range(len(actual_array), len(expected_array)))
                mismatched_indices.extend(missing_indices)
            else:
                # Extra elements at the end
                extra_indices = list(range(len(expected_array), len(actual_array)))
                mismatched_indices.extend(extra_indices)

        if mismatched_indices:
            # Calculate matched count
            matched_count = min_length - len([i for i in mismatched_indices if i < min_length])
            total_expected = len(expected_array)

            # Format arrays for display
            expected_display = self._format_array_for_display(expected_array)
            actual_display = self._format_array_for_display(actual_array)

            # Only add summary assertion if we don't already have detailed nested assertions
            # or if there's a length mismatch
            if len(expected_array) != len(actual_array) or not assertions:
                assertions.append(
                    EvalAssertion.create(
                        assertion_name=f"{value_name}_array_values_mismatch",
                        status=EvalStatus.FAILURE,
                        assertion_msgs=[
                            f"Array value mismatch (ordered). Matched ({matched_count}/{total_expected})",
                            f"Expected: {expected_display}, Got: {actual_display}",
                        ],
                    )
                )

        return assertions

    def _compare_objects(
        self,
        *,
        expected_object: dict | MappingProxyType,
        actual_object: Any,
        value_name: str,
        ignored_values_keys: set | None = None,
        ignore_extra_keys: bool = False,
        ordered: bool = False,
        visited: set[int] | None = None,
        **kwargs: Any,
    ) -> list[EvalAssertion]:
        """Compare object structures key-by-key.

        Validates keys match (unless ignore_extra_keys=True), then recursively
        compares values for common keys.

        Args:
            expected_object: Expected object (dict or MappingProxyType)
            actual_object: Actual value (validated to be dict-like)
            value_name: Path name for error messages
            ignored_values_keys: Keys to skip during value comparison
            ignore_extra_keys: Whether to allow extra keys in actual
            ordered: Whether nested sequences are order-sensitive
            visited: Set of visited object IDs for circular reference detection

        Returns:
            List of EvalAssertion (empty if match)
        """
        if not isinstance(expected_object, (dict, MappingProxyType)):
            raise TypeError(f"Expected object must be dict or MappingProxyType, got {type(expected_object).__name__}")

        # Check if actual is a structured object
        if not isinstance(actual_object, (dict, MappingProxyType)):
            return [
                EvalAssertion.create(
                    assertion_name=f"{value_name}_invalid_format",
                    status=EvalStatus.FAILURE,
                    assertion_msgs=[f"Expected a structured object, but got: {type(actual_object).__name__}"],
                )
            ]

        # compare values
        ref_keys = set(expected_object.keys())
        if len(ref_keys) == 0:
            raise ValueError("Expected object must have at least one key")

        actual_keys = set(actual_object.keys())

        missing_keys = ref_keys - actual_keys
        extra_keys = actual_keys - ref_keys

        assertions = []
        if missing_keys or extra_keys:
            msgs = []
            if extra_keys and not ignore_extra_keys:
                msgs.append(f"Extra keys in actual object: {sorted(extra_keys)}")
            if missing_keys:
                msgs.append(f"Missing keys in actual object: {sorted(missing_keys)}")

            # Only create assertion if there are actual error messages
            if msgs:
                assertions.append(
                    EvalAssertion.create(
                        assertion_name=f"{value_name}_keys_mismatch",
                        status=EvalStatus.FAILURE,
                        assertion_msgs=msgs,
                    )
                )

        keys_for_value_check = ref_keys & actual_keys
        if ignored_values_keys:
            keys_for_value_check -= set(ignored_values_keys)

        # Recursively compare values for each key
        for k in keys_for_value_check:
            nested_assertions = self._compare_recursive(
                actual=actual_object[k],
                expected=expected_object[k],
                ordered=ordered,
                path=f"{value_name}.{k}",
                ignored_values_keys=ignored_values_keys,
                ignore_extra_keys=ignore_extra_keys,
                visited=visited,
                **kwargs,
            )
            assertions.extend(nested_assertions)

        return assertions

    def _compare_recursive(
        self,
        actual: Any,
        expected: Any,
        ordered: bool,
        path: str,
        ignored_values_keys: set | None = None,
        ignore_extra_keys: bool = False,
        visited: set[int] | None = None,
        **kwargs: Any,
    ) -> list[EvalAssertion]:
        """Recursively compare values with circular reference protection.

        Dispatches to specialized methods based on expected type (dict, list, or primitive).
        Detects circular references by tracking visited object IDs.

        Args:
            actual: Actual value
            expected: Expected value
            ordered: Whether order matters for arrays
            path: Current path for error messages (e.g., "value.items[0]")
            ignored_values_keys: Object keys to skip during comparison
            ignore_extra_keys: Whether to allow extra keys in actual objects
            visited: Object IDs already visited (for circular reference detection)

        Returns:
            List of EvalAssertion (empty = success)

        Raises:
            ValueError: If circular reference detected in actual value
        """
        # Initialize visited set if not provided (for backwards compatibility)
        if visited is None:
            visited = set()

        # Check for circular references in container types
        # Only check actual value (we control expected, it shouldn't have circular refs)
        if isinstance(actual, (dict, MappingProxyType, list, tuple)):
            actual_id = id(actual)
            if actual_id in visited:
                raise ValueError(
                    f"Circular reference detected at path '{path}'. "
                    f"Object has already been visited during comparison. "
                    f"This indicates the actual value contains a circular reference, "
                    f"which is not supported for comparison."
                )
            visited.add(actual_id)

        # Handle None values
        if expected is None and actual is None:
            return []

        if expected is None or actual is None:
            return [
                EvalAssertion.create(
                    assertion_name=f"{path}_none_mismatch",
                    status=EvalStatus.FAILURE,
                    assertion_msgs=[f"Expected {expected}, got {actual}"],
                )
            ]

        # Dispatch based on expected type
        if isinstance(expected, (dict, MappingProxyType)):
            return self._compare_objects(
                expected_object=expected,
                actual_object=actual,
                value_name=path,
                ordered=ordered,  # Pass down for nested arrays
                ignored_values_keys=ignored_values_keys,
                ignore_extra_keys=ignore_extra_keys,
                visited=visited,
                **kwargs,
            )
        if isinstance(expected, (list, tuple)):
            return self._compare_arrays(
                expected_array=expected,
                actual_array=actual,
                value_name=path,
                ordered=ordered,
                ignored_values_keys=ignored_values_keys,
                ignore_extra_keys=ignore_extra_keys,
                visited=visited,
                **kwargs,
            )
        # Direct comparison for all other types (NormalizedType and primitives)
        # NormalizedType.__eq__ handles alternatives automatically
        if expected != actual:
            return [
                EvalAssertion.create(
                    assertion_name=f"{path}_mismatch",
                    status=EvalStatus.FAILURE,
                    assertion_msgs=[f"Expected {expected}, got {actual}"],
                )
            ]
        return []

    def _format_value(self, value: Any) -> Any:
        """Format value for display in error messages.

        Extracts normalized value from NormalizedType instances.

        Args:
            value: Value to format

        Returns:
            Formatted value (.normalized for NormalizedType, otherwise unchanged)
        """
        if isinstance(value, NormalizedType):
            return value.normalized
        return value

    def _format_array_for_display(self, array: list | tuple) -> str:
        """Format array for display in error messages.

        Shows first 2 and last 1 elements with ellipsis for arrays longer than 3 elements.

        Args:
            array: Array to format

        Returns:
            Formatted string (e.g., "[1, 2, ..., 5]" or "[1, 2, 3]")
        """
        if len(array) == 0:
            return "[]"

        # Format each element
        formatted_elements = [str(self._format_value(elem)) for elem in array]

        # If array is short, show all elements
        if len(formatted_elements) <= 3:
            return f"[{', '.join(formatted_elements)}]"

        # Otherwise, show first 2 and last 1 with ellipsis
        return f"[{formatted_elements[0]}, {formatted_elements[1]}, ..., {formatted_elements[-1]}]"
```

### `official/src/webarena_verified/core/evaluation/value_normalizer.py`

Source ref: `https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/core/evaluation/value_normalizer.py`

```python
"""Value normalization with schema-driven type resolution and alternatives support."""

import json
import logging
from types import MappingProxyType
from typing import Any

from webarena_verified.core.evaluation.data_types import TYPE_REGISTRY, NormalizedString, NormalizedType

logger = logging.getLogger(__name__)


class ValueNormalizer:
    """Normalizes values using TYPE_REGISTRY and NormalizedType classes.

    Responsibilities:
    - Extract type from JSON schema
    - Look up NormalizedType class from TYPE_REGISTRY
    - Create NormalizedType instances (handles normalization internally)
    - Support single values, arrays, and objects
    - Detect and handle alternatives (when value is a list)

    Examples:
        normalizer = ValueNormalizer()

        # Single value with schema
        normalized = normalizer.normalize("success", {"type": "string"}, strict=True)
        # → NormalizedString("success")

        # Single value with alternatives
        normalized = normalizer.normalize(["success", "ok"], {"type": "string"}, strict=True)
        # → NormalizedString(["success", "ok"])

        # Array with element-level alternatives
        normalized = normalizer.normalize([[10, 17], 15], {"type": "array", "items": {"format": "number"}}, strict=True)
        # → [NormalizedNumber([10, 17]), NormalizedNumber(15)]

        # Object with property-level alternatives
        normalized = normalizer.normalize(
            {"status": ["success", "ok"], "code": 200},
            {"type": "object", "properties": {"status": {"type": "string"}, "code": {"format": "number"}}},
            strict=True
        )
        # → {"status": NormalizedString(["success", "ok"]), "code": NormalizedNumber(200)}
    """

    def _get_normalized_type_class(self, item_type: dict | None) -> type[NormalizedType]:
        if item_type is None:
            return NormalizedString  # Default to string type

        if type_format := item_type.get("format"):
            type_name = type_format
        else:
            type_name = item_type.get("type", "string")  # Default to string if not specified

        if type_name not in TYPE_REGISTRY:
            raise ValueError(f"Unknown type name: {type_name!r} during normalization")
        return TYPE_REGISTRY[type_name]

    def _normalize_simple_value(
        self, original_value: Any, item_type: dict | None, strict: bool = True, **kwargs: Any
    ) -> NormalizedType | Any:
        type_class = self._get_normalized_type_class(item_type)

        try:
            return type_class(original_value, **kwargs)
        except Exception as e:
            if strict:
                raise ValueError(
                    f"Failed to normalize value {original_value!r} with type {type_class.__name__!r}"
                ) from e
            logger.debug(
                f"Normalization failed for value {original_value!r} with type {type_class.__name__!r}: {e}",
                exc_info=True,
            )
            return original_value

    def normalize_object(
        self, value: Any, schema: dict | MappingProxyType | None, strict: bool = True, **kwargs: Any
    ) -> MappingProxyType | None:
        """Normalize a dict/object value according to schema."""
        if schema:
            if not isinstance(schema, (dict, MappingProxyType)):
                raise TypeError(f"Schema must be dict or MappingProxyType, got {type(schema).__name__}")
        else:
            return None

        if not strict and isinstance(value, str):
            # Try json parsing for strings
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict) or (
                    isinstance(parsed, (list, tuple)) and len(parsed) == 1 and isinstance(parsed[0], dict)
                ):
                    value = parsed
            except json.JSONDecodeError:
                pass

        if not isinstance(value, (dict, MappingProxyType)):
            if strict:
                raise ValueError(f"Property '{value}' schema expects array but got {type(value).__name__}")
            return None

        properties = schema.get("properties", {})
        normalized = {}
        for field_name, field_schema in properties.items():
            if field_name not in value:
                normalized[field_name] = None
                continue

            field_type = field_schema.get("type")
            if field_type == "array":
                normalized[field_name] = self.normalize_array(value[field_name], field_schema, strict, **kwargs)
            else:
                normalized[field_name] = self._normalize_simple_value(value[field_name], field_schema, strict, **kwargs)

        return MappingProxyType(normalized)

    def normalize_array(  # noqa: C901
        self, value: Any, schema: dict | MappingProxyType | None, strict: bool = True, **kwargs: Any
    ) -> tuple | None:
        """Normalize an array/list value according to schema."""
        if schema and not isinstance(schema, (dict, MappingProxyType)):
            raise TypeError(f"Schema must be dict or MappingProxyType, got {type(schema).__name__}")

        if not strict:
            if isinstance(value, str):
                # Try json parsing for strings
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, (list, tuple)):
                        value = parsed
                except json.JSONDecodeError:
                    pass

            if not isinstance(value, (list, tuple)):
                value = (value,)

        if not isinstance(value, (list, tuple)):
            if strict:
                raise ValueError(f"Property '{value}' schema expects array but got {type(value).__name__}")
            return None

        # Handle schema=None by defaulting to string type for array elements
        if schema is None:
            items_schema = None  # Will default to NormalizedString in _normalize_simple_value
            items_type = "string"
        else:
            schema_type = schema.get("type", "array")
            if schema_type != "array":
                raise ValueError(f"Schema type must be 'array', got: {schema_type!r}")

            items_schema = schema.get("items", {})
            items_type = items_schema.get("type", "string")  # Default to string if not specified

        if items_type == "object":
            # Handle list of objects
            # Note: items_schema cannot be None here because items_type is only "object" when schema is provided
            if items_schema is None:
                raise ValueError("items_schema must be provided when items_type is 'object'")
            normalized_array = tuple(
                [self._normalize_object_or_array(item, items_schema, strict, **kwargs) for item in value]
            )
        else:
            # Handle list of simple types
            normalized_array = tuple(
                [self._normalize_simple_value(item, items_schema, strict, **kwargs) for item in value]
            )

        return tuple(normalized_array)

    def normalize(
        self, value: Any, schema: dict | MappingProxyType, strict: bool = True, **kwargs: Any
    ) -> NormalizedType | tuple[NormalizedType, ...] | tuple[dict, ...] | dict | MappingProxyType | None:
        """Main entry point for normalization.

        Args:
            value: Raw value to normalize (single, array, or object)
            schema: JSON schema defining the type
            strict: If True, raise on normalization errors (for expected)
                   If False, return raw value on error (for actual)

        Returns:
            Normalized value (NormalizedType instances, tuple, or dict)
            Returns None for None/empty values
            Arrays are returned as tuple for immutability

        Examples:
            # With schema
            normalize("yes", {"type": "boolean"}, strict=True)
            # → Boolean(True)

            # Array with schema
            normalize([10, 15], {"type": "array", "items": {"format": "number"}}, strict=True)
            # → (NormalizedNumber(10), NormalizedNumber(15))
        """
        # Handle None/empty values
        if not value:
            return None

        if not schema:
            if isinstance(value, (dict, MappingProxyType)):
                schema = {"type": "object"}
            elif isinstance(value, (list, tuple)):
                schema = {"type": "array"}

        type_name_or_schema, is_array = self._extract_type_from_schema(schema)

        # Check if we got an object schema instead of a type name
        if isinstance(type_name_or_schema, (dict, MappingProxyType)):
            # Handle object schema with property-by-property normalization
            return self._normalize_object_or_array(value, type_name_or_schema, strict, **kwargs)

        # Handle array vs single value based on schema
        if is_array:
            # Schema indicates array - normalize as array
            if not isinstance(value, (list, tuple)):
                # Value should be an array but isn't - error or coerce?
                if strict:
                    raise ValueError(f"Schema expects array but got {type(value).__name__}: {value!r}")
                return value  # Return raw value in non-strict mode
            return self._normalize_array(value, type_name_or_schema, strict, **kwargs)
        # Schema indicates single value
        # If value is list at root level, treat as alternatives
        return self.normalize_single(value, type_name_or_schema, strict, **kwargs)

    def normalize_single(self, value: Any, type_name: str, strict: bool, **kwargs: Any) -> NormalizedType:
        """Normalize single value with alternative detection.

        Args:
            value: Raw value (single value or list of alternatives)
            type_name: Type name from TYPE_REGISTRY
            strict: If True, raise on normalization errors

        Returns:
            NormalizedType instance (may contain alternatives internally)

        Examples:
            # Single value
            _normalize_single("success", "string", strict=True)
            # → NormalizedString("success")

            # Multiple alternatives
            _normalize_single(["success", "ok"], "string", strict=True)
            # → NormalizedString(["success", "ok"])
        """
        if type_name not in TYPE_REGISTRY:
            raise ValueError(f"Unknown type name: {type_name!r}")

        type_class = TYPE_REGISTRY[type_name]

        try:
            # NormalizedType handles both single values and lists (alternatives)
            return type_class(value, **kwargs)
        except Exception as e:
            logger.debug(f"Normalization failed for value {value!r} with type {type_name!r}: {e}", exc_info=True)
            if strict:
                raise
            # In non-strict mode, return raw value on normalization failure
            return value

    def _normalize_array(
        self,
        value: list | tuple | str,
        type_name: str | dict | MappingProxyType,
        strict: bool,
        **kwargs: Any,
    ) -> tuple[NormalizedType, ...] | Any:
        """Normalize array, detecting element-level alternatives.

        Args:
            value: List or tuple of values (each can be single or list of alternatives)
            type_name: Type name from TYPE_REGISTRY for array elements
            strict: If True, raise on normalization errors

        Returns:
            Tuple of NormalizedType instances

        Examples:
            # Array without alternatives
            _normalize_array(("apple", "banana"), "string", strict=True)
            # → (NormalizedString("apple"), NormalizedString("banana"))

            # Array with element-level alternatives
            _normalize_array(([10, 17], 15), "number", strict=True)
            # → (NormalizedNumber([10, 17]), NormalizedNumber(15))
        """
        if isinstance(value, str):
            # Try json parsing for strings
            try:
                parsed = json.loads(value)
                if isinstance(parsed, (list, tuple)):
                    value = parsed
            except json.JSONDecodeError:
                pass
        if not isinstance(value, (list, tuple)):
            if strict:
                raise ValueError(f"Property '{value}' schema expects array but got {type(value).__name__}")
            return value  # Return raw value in non-strict mode
        if isinstance(type_name, (dict, MappingProxyType)):
            return self._normalize_object_or_array(value, type_name, strict, **kwargs)
        if type_name not in TYPE_REGISTRY:
            raise ValueError(f"Unknown type name: {type_name!r}")

        type_class = TYPE_REGISTRY[type_name]
        result = []

        for i, item in enumerate(value):
            try:
                # Each item can be:
                # 1. A single value → NormalizedType(item)
                # 2. A list of alternatives → NormalizedType([alt1, alt2, ...])
                # The NormalizedType constructor handles both cases
                result.append(type_class(item, **kwargs))
            except Exception as e:
                if strict:
                    raise ValueError(f"Failed to normalize array element at index {i}: {item!r}") from e
                # In non-strict mode, keep raw value
                result.append(item)

        return tuple(result)

    def _normalize_object_or_array(
        self,
        value: dict | MappingProxyType | list[dict] | tuple[dict, ...],
        object_schema: dict | MappingProxyType,
        strict: bool,
        **kwargs: Any,
    ) -> dict | tuple[dict, ...]:
        """Normalize object or array of objects.

        Args:
            value: Object or array of objects
            object_schema: Object schema with properties
            strict: If True, raise on normalization errors

        Returns:
            Normalized object or tuple of objects
        """
        if isinstance(value, (list, tuple)):
            # Array of objects
            return tuple(self._normalize_object(obj, object_schema, strict, **kwargs) for obj in value)
        # Single object
        return self._normalize_object(value, object_schema, strict, **kwargs)

    def _normalize_object(  # noqa: C901, PLR0912
        self,
        obj: dict | MappingProxyType,
        object_schema: dict | MappingProxyType,
        strict: bool,
        **kwargs: Any,
    ) -> dict:
        """Normalize object with property-level alternatives.

        Args:
            obj: Dictionary with properties
            object_schema: Object schema with property definitions
            strict: If True, raise on normalization errors

        Returns:
            Dictionary with normalized property values

        Examples:
            # Object without alternatives
            _normalize_object(
                {"status": "success", "code": 200},
                {"properties": {"status": {"type": "string"}, "code": {"format": "number"}}},
                strict=True
            )
            # → {"status": NormalizedString("success"), "code": NormalizedNumber(200)}

            # Object with property-level alternatives
            _normalize_object(
                {"status": ["success", "ok"], "code": 200},
                {"properties": {"status": {"type": "string"}, "code": {"format": "number"}}},
                strict=True
            )
            # → {"status": NormalizedString(["success", "ok"]), "code": NormalizedNumber(200)}
        """
        if isinstance(obj, MappingProxyType):
            obj = dict(obj)
        elif isinstance(obj, str):
            # Try json parsing for strings
            try:
                parsed = json.loads(obj)
                if isinstance(parsed, dict):
                    obj = parsed
            except json.JSONDecodeError:
                pass

        if not isinstance(obj, dict):
            if strict:
                raise ValueError(f"Expected dict for object normalization, got {type(obj).__name__}: {obj!r}")
            return obj

        # Get property schemas
        properties = object_schema.get("properties", {})
        normalized = {}

        for prop_name, prop_value in obj.items():
            # Handle None values - don't attempt normalization
            if prop_value is None:
                normalized[prop_name] = None
                continue

            # Get property schema
            prop_schema = properties.get(prop_name)

            if prop_schema is None:
                # No schema for this property - fall back to NormalizedString
                try:
                    normalized[prop_name] = NormalizedString(prop_value, **kwargs)
                except Exception:
                    if strict:
                        raise
                    normalized[prop_name] = prop_value
                continue

            # Extract type from property schema
            prop_type_name, is_array = self._extract_type_from_schema(prop_schema)

            # Normalize property value (handles alternatives automatically)
            try:
                if is_array:
                    normalized[prop_name] = self._normalize_array(prop_value, prop_type_name, strict, **kwargs)
                elif isinstance(prop_type_name, str) and prop_type_name in TYPE_REGISTRY:
                    type_class = TYPE_REGISTRY[prop_type_name]
                    normalized[prop_name] = type_class(prop_value, **kwargs)
                elif isinstance(prop_type_name, (dict, MappingProxyType)):
                    # Recursively normalize nested object
                    normalized[prop_name] = self._normalize_object(prop_value, prop_type_name, strict, **kwargs)
                else:
                    # Unknown type, fall back to NormalizedString or keep raw
                    normalized[prop_name] = NormalizedString(prop_value, **kwargs)
            except Exception as e:
                if strict:
                    raise ValueError(f"Failed to normalize property '{prop_name}': {prop_value!r}") from e
                # In non-strict mode, keep raw value
                normalized[prop_name] = prop_value

        return normalized

    def _extract_type_from_schema(
        self, schema: dict | MappingProxyType
    ) -> tuple[str | dict[str, Any] | MappingProxyType[str, Any], bool]:
        """Extract type information from JSON schema.

        Args:
            schema: JSON schema

        Returns:
            Tuple of (type_name_or_schema, is_array)
            - type_name_or_schema: Either a string (type name) or dict (object schema)
            - is_array: True if schema indicates an array

        Examples:
            # Simple type
            _extract_type_from_schema({"type": "string"})
            # → ("string", False)

            # Format-based type
            _extract_type_from_schema({"type": "string", "format": "currency"})
            # → ("currency", False)

            # Array type
            _extract_type_from_schema({"type": "array", "items": {"format": "number"}})
            # → ("number", True)

            # Object type
            _extract_type_from_schema({"type": "object", "properties": {...}})
            # → ({properties...}, False)
        """
        if not isinstance(schema, (dict, MappingProxyType)):
            raise ValueError(f"Schema must be dict or MappingProxyType, got {type(schema).__name__}")

        schema_type = schema.get("type")

        # Handle array type
        if schema_type == "array":
            items_schema = schema.get("items", {})
            # Extract type from items schema
            item_type, _ = self._extract_type_from_schema(items_schema)
            return (item_type, True)  # is_array=True

        # Handle object type
        if schema_type == "object":
            # Return the entire schema for object handling
            return (schema, False)  # is_array=False

        # Handle simple types with optional format
        # Format takes precedence (e.g., "format": "currency" overrides "type": "string")
        format_type = schema.get("format")
        if format_type:
            return (format_type, False)

        # Fall back to base type
        if schema_type:
            return (schema_type, False)

        # No type information - default to string
        return ("string", False)
```

### `official/src/webarena_verified/types/agent_response.py`

Source ref: `https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/types/agent_response.py`

```python
from enum import StrEnum
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

# Public type for external agent responses (no lists - agents return single values)
PublicResultItem = str | int | float | bool | dict[str, Any] | None

# Internal type for evaluation (includes lists to support alternatives in expected values)
# Supports nested lists for alternatives like [["item1", "item2"], ["item3", "item4"]]
InternalResultItem = PublicResultItem | list[str | int | float | bool | dict[str, Any] | None]


class MainObjectiveType(StrEnum):
    """Used to indicate the overall type of work performed to attain the task objective.

    Attributes:
        RETRIEVE: Use retrieving data is the main objective of the task
        MUTATE: Use when creating, updating, or deleting data or state is the main objective of the task
        NAVIGATE: Use when navigating or browsing to show a specific page or location is the main objective of the task
    """

    RETRIEVE = "RETRIEVE"
    MUTATE = "MUTATE"
    NAVIGATE = "NAVIGATE"


# Backward compatibility alias
PerformedOperation = MainObjectiveType


class Status(StrEnum):
    """Used to indicate the outcome of the task execution.

    Attributes:
        SUCCESS: Use when the task objective was fully achieved
        ACTION_NOT_ALLOWED_ERROR: Use when the platform does not support the requested action
            or is not allowed in the current context or state
        NOT_FOUND_ERROR: Use when the target entity or resource could not be located
            after retry attempts
        PERMISSION_DENIED_ERROR: Use when the current user lacks permission to perform the action
        DATA_VALIDATION_ERROR: Use when required input data was missing or invalid
        UNKNOWN_ERROR: Use when an unexpected failure doesn't match other categories
    """

    SUCCESS = "SUCCESS"
    ACTION_NOT_ALLOWED_ERROR = "ACTION_NOT_ALLOWED_ERROR"
    PERMISSION_DENIED_ERROR = "PERMISSION_DENIED_ERROR"
    NOT_FOUND_ERROR = "NOT_FOUND_ERROR"
    DATA_VALIDATION_ERROR = "DATA_VALIDATION_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class FinalAgentResponse(BaseModel):
    """Final response format for agent task execution.

    The agent must respond with valid JSON containing the task type, task outcome status,
    retrieved data (for retrieve operations), and error details (when applicable).

    Attributes:
        task_type (required): The type of task performed (RETRIEVE, MUTATE, or NAVIGATE)
        status (required): The outcome of the task execution
        retrieved_data: Array of items for 'retrieve' operations, null for
            'mutate' and 'navigate' operations. Returns empty array if no items found.
            All items must be the same type (either all primitives of the same type,
            or all objects with the same keys). Use appropriate data type formats
            (e.g., numbers for amounts/counts, true/false for booleans, not strings).
            For list of objects, the user instruction contains the format specification.
        error_details: Null when status is 'SUCCESS'. Otherwise, explains used to explain the failure reason concisely.
    """

    task_type: MainObjectiveType = Field(validation_alias=AliasChoices("task_type", "performed_operation"))
    status: Status
    retrieved_data: list[PublicResultItem] | None = None
    error_details: str | None = None

    model_config = ConfigDict(use_enum_values=True, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def normalize_case(cls, data: Any) -> Any:
        """Normalize task_type and status to uppercase for case-insensitive parsing."""
        if isinstance(data, dict):
            # Handle new field name and legacy field name
            if "task_type" in data and isinstance(data["task_type"], str):
                data["task_type"] = data["task_type"].upper()
            if "performed_operation" in data and isinstance(data["performed_operation"], str):
                data["performed_operation"] = data["performed_operation"].upper()
            if "status" in data and isinstance(data["status"], str):
                data["status"] = data["status"].upper()
        return data

    @property
    def is_retrieve(self) -> bool:
        """Check if the task type is RETRIEVE."""
        return self.task_type == MainObjectiveType.RETRIEVE

    @property
    def is_navigate(self) -> bool:
        """Check if the task type is NAVIGATE."""
        return self.task_type == MainObjectiveType.NAVIGATE

    @property
    def is_mutate(self) -> bool:
        """Check if the task type is MUTATE."""
        return self.task_type == MainObjectiveType.MUTATE


class _FinalAgentResponse(FinalAgentResponse):
    """Internal version for loading expected values with alternatives.

    Used only when parsing task definitions that may contain alternative
    values (e.g., ["success", "ok"] means either is acceptable).
    Never exposed to public users - the public schema comes from FinalAgentResponse.
    """

    retrieved_data: list[InternalResultItem] | None = None

    @classmethod
    def model_json_schema(cls, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        """Return public schema from parent class to hide internal implementation."""
        return FinalAgentResponse.model_json_schema(**kwargs)
```

### `official/src/webarena_verified/types/eval.py`

Source ref: `https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/types/eval.py`

```python
import datetime
from enum import StrEnum
from importlib.metadata import version
from types import MappingProxyType
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, model_serializer

from ..core.utils.checksum import compute_evaluator_checksum
from .common import SerializableMappingProxyType
from .config import WebArenaVerifiedConfig
from .task import WebArenaSite, WebArenaVerifiedTask
from .tracing import NetworkTrace

WEBARENA_VERIFIED_VERSION = version("webarena-verified")  # Read from pyproject metadata


class SiteEvalResultsSummary(BaseModel):
    """Evaluation summary for a single site."""

    total: int = 0
    success_count: int = 0
    failure_count: int = 0
    error_count: int = 0
    failed_or_error_count: int = 0
    success_task_ids: list[int] = []
    failed_task_ids: list[int] = []
    error_task_ids: list[int] = []


class OverallEvalSummary(BaseModel):
    """Overall evaluation summary across all sites."""

    total: int = 0
    success_count: int = 0
    failure_count: int = 0
    error_count: int = 0
    failed_or_error_count: int = 0


class EvalResultsSummary(BaseModel):
    """Combined evaluation summary with overall and per-site breakdowns."""

    overall: OverallEvalSummary
    per_site: dict[str, SiteEvalResultsSummary]


class EvalStatus(StrEnum):
    """Evaluation result status."""

    SUCCESS = "success"
    PARTIAL_MATCH = "partial_match"
    FAILURE = "failure"
    ERROR = "error"


class EvalAssertion(BaseModel):
    """Single assertion result within an evaluation."""

    assertion_name: str
    status: EvalStatus
    assertion_msgs: tuple[str, ...] | None = None
    error_msg: str | None = None

    model_config = ConfigDict(frozen=True, use_enum_values=True)

    @property
    def is_success(self) -> bool:
        """Check if assertion passed."""
        return self.status == EvalStatus.SUCCESS

    @classmethod
    def create(
        cls,
        *,
        assertion_name: str,
        assertion_msgs: list[str] | None = None,
        status: EvalStatus,
        error_msg: str | None = None,
    ) -> Self:
        """Create an EvalAssertion instance."""
        if status == EvalStatus.ERROR:
            assert error_msg is not None, "Error message must be provided for ERROR status"

        return cls(
            assertion_name=assertion_name,
            status=status,
            assertion_msgs=tuple(assertion_msgs) if assertion_msgs else None,
            error_msg=error_msg,
        )


class EvaluatorResult(BaseModel):
    """Result from a single evaluator."""

    evaluator_name: str
    status: EvalStatus
    score: float
    actual: Any | None = None
    actual_normalized: Any | None = None
    expected: Any | None = None
    assertions: tuple[EvalAssertion, ...] | None = None
    error_msg: str | None = None
    should_not_exist: bool | None = None

    model_config = ConfigDict(frozen=True, use_enum_values=True)

    @model_serializer
    def _serialize_model(self) -> dict[str, Any]:
        """Custom serializer to handle MappingProxyType and NormalizedType instances.

        Converts both MappingProxyType (to dict) and NormalizedType instances (to their
        normalized values) for JSON serialization. These types can appear nested in dicts
        or lists where Pydantic's type-based serialization doesn't automatically apply.
        """
        from webarena_verified.core.evaluation.data_types import NormalizedType  # noqa: PLC0415 (circular import)

        def convert_to_serializable(obj: Any) -> Any:
            if isinstance(obj, (MappingProxyType, dict)):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [convert_to_serializable(item) for item in obj]
            if isinstance(obj, NormalizedType):
                # Extract normalized value from NormalizedType instances
                return obj.normalized
            return obj

        return {
            "evaluator_name": self.evaluator_name,
            "status": self.status,
            "score": self.score,
            "actual": convert_to_serializable(self.actual),
            "actual_normalized": convert_to_serializable(self.actual_normalized),
            "expected": convert_to_serializable(self.expected),
            "assertions": self.assertions,
            "error_msg": self.error_msg,
            "should_not_exist": self.should_not_exist,
        }

    @classmethod
    def create(  # noqa: PLR0913
        cls,
        *,
        evaluator_name: str,
        assertions: list[EvalAssertion] | None = None,
        error_msg: str | None = None,
        is_error: bool = False,
        actual: Any | None = None,
        actual_normalized: Any | None = None,
        expected: Any | None = None,
        should_not_exist: bool | None = None,
    ) -> Self:
        """Create an EvaluatorResult with computed status and score."""
        if is_error:
            # Case where the evaluator itself encountered an error
            assert error_msg is not None, "Error message must be provided for ERROR status"
            status = EvalStatus.ERROR
            score = 0.0
        else:
            # Empty assertion list means all validations passed (no differences found)
            if assertions is None or len(assertions) == 0:
                status = EvalStatus.SUCCESS
                score = 1.0
            elif any(a.status == EvalStatus.ERROR for a in assertions):
                # Case where one or more assertions resulted in an error
                status = EvalStatus.ERROR
                score = 0.0
            else:
                # All assertions are either SUCCESS or FAILURE
                score = 1.0 if all(a.is_success for a in assertions) else 0.0
                status = EvalStatus.SUCCESS if score == 1.0 else EvalStatus.FAILURE

        return cls(
            evaluator_name=evaluator_name,
            status=status,
            score=score,
            actual=actual,
            actual_normalized=actual_normalized,
            expected=expected,
            assertions=tuple(assertions) if assertions else None,
            error_msg=error_msg,
            should_not_exist=should_not_exist,
        )


class TaskEvalResult(BaseModel):
    """Evaluation result for a single task."""

    task_id: int
    intent_template_id: int
    sites: tuple[WebArenaSite, ...]
    task_revision: int
    status: EvalStatus
    score: float
    evaluators_results: tuple[EvaluatorResult, ...]
    error_msg: str | None = None
    webarena_verified_version: str = WEBARENA_VERIFIED_VERSION
    webarena_verified_evaluator_checksum: str = compute_evaluator_checksum()
    webarena_verified_data_checksum: str

    @classmethod
    def create(  # noqa: PLR0913
        cls,
        *,
        task_id: int,
        intent_template_id: int,
        sites: tuple[WebArenaSite, ...],
        task_revision: int,
        data_checksum: str,
        evaluators_results: list[EvaluatorResult] | None = None,
        error_msg: str | None = None,
        is_error: bool = False,
    ) -> Self:
        """Create a TaskEvalResult with computed status and score."""
        if is_error:
            # Case where the task eval encountered an error
            assert error_msg is not None, "Error message must be provided for ERROR status"
            status = EvalStatus.ERROR
            score = 0.0
            evaluators_results = evaluators_results or []
        else:
            assert evaluators_results is not None, "Evaluator results cannot be None."
            assert len(evaluators_results) > 0, "At least one evaluator result is required."
            if any(er.status == EvalStatus.ERROR for er in evaluators_results):
                # Case where one or more evaluators resulted in an error
                status = EvalStatus.ERROR
                score = 0.0
            else:
                score = 1.0 if all(er.score == 1.0 for er in evaluators_results) else 0.0
                status = EvalStatus.SUCCESS if score == 1.0 else EvalStatus.FAILURE

        return cls(
            task_id=task_id,
            intent_template_id=intent_template_id,
            sites=sites,
            task_revision=task_revision,
            status=status,
            score=score,
            evaluators_results=tuple(evaluators_results),
            error_msg=error_msg,
            webarena_verified_data_checksum=data_checksum,
        )


class TasksEvalResults(BaseModel):
    """Collection of evaluation results for multiple tasks."""

    timestamp: str
    webarena_verified_version: str = WEBARENA_VERIFIED_VERSION
    webarena_verified_evaluator_checksum: str = compute_evaluator_checksum()
    webarena_verified_data_checksum: str
    summary: EvalResultsSummary
    task_results: tuple[TaskEvalResult, ...]

    model_config = ConfigDict(frozen=True)

    @classmethod
    def create(cls, *, task_results: list[TaskEvalResult] | tuple[TaskEvalResult], data_checksum: str) -> Self:
        """Create TasksEvalResults with computed summary."""
        timestamp = datetime.datetime.now(datetime.UTC).isoformat()
        summary = cls._compute_summary(task_results)

        return cls(
            timestamp=timestamp,
            summary=summary,
            task_results=tuple(task_results),
            webarena_verified_data_checksum=data_checksum,
        )

    @staticmethod
    def _compute_summary(
        task_results: list[TaskEvalResult] | tuple[TaskEvalResult, ...],
    ) -> EvalResultsSummary:
        """Compute overall and per-site summary statistics from task results."""
        per_site: dict[str, SiteEvalResultsSummary] = {}
        overall = OverallEvalSummary()

        for result in task_results:
            site_key = "-".join(sorted(result.sites))

            if site_key not in per_site:
                per_site[site_key] = SiteEvalResultsSummary()

            per_site[site_key].total += 1
            overall.total += 1

            if result.status == EvalStatus.SUCCESS:
                per_site[site_key].success_count += 1
                per_site[site_key].success_task_ids.append(result.task_id)
                overall.success_count += 1
            elif result.status == EvalStatus.FAILURE:
                per_site[site_key].failure_count += 1
                per_site[site_key].failed_task_ids.append(result.task_id)
                overall.failure_count += 1
            elif result.status == EvalStatus.ERROR:
                per_site[site_key].error_count += 1
                per_site[site_key].error_task_ids.append(result.task_id)
                overall.error_count += 1

            if result.status != EvalStatus.SUCCESS:
                per_site[site_key].failed_or_error_count += 1
                overall.failed_or_error_count += 1

        return EvalResultsSummary(overall=overall, per_site=per_site)


class TransformedAgentResponse(BaseModel):
    """Used when an agent response is transformed before evaluation."""

    original_response: Any
    transformed_response: SerializableMappingProxyType | None = None

    @classmethod
    def create(cls, *, original_response: Any, transformed_response: dict[str, Any] | MappingProxyType) -> Self:
        """Create a TransformedAgentResponse instance."""
        assert isinstance(transformed_response, (dict, MappingProxyType))
        return cls(
            original_response=original_response,
            transformed_response=transformed_response,  # type: ignore
        )


class TaskEvalContext(BaseModel):
    """Context passed to evaluators during task evaluation."""

    task: WebArenaVerifiedTask
    agent_response_raw: Any | TransformedAgentResponse | None = None
    network_trace: NetworkTrace
    config: WebArenaVerifiedConfig

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)
```

### `official/src/webarena_verified/types/task.py`

Source ref: `https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/types/task.py`

```python
"""Data models for WebArena Verified tasks (version >= 2.0.0)."""

from enum import StrEnum
from typing import Annotated, Any, Generic, Literal, Self, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .agent_response import FinalAgentResponse, _FinalAgentResponse
from .common import NonEmptyStr, QueryParams, SerializableMappingProxyType


# ============================================================================
# Site Enum
# ============================================================================
class WebArenaSite(StrEnum):
    """Supported web platforms in the WebArena benchmark.

    Each site represents a different web application environment where tasks are executed.
    """

    GITLAB = "gitlab"
    MAP = "map"
    REDDIT = "reddit"
    SHOPPING_ADMIN = "shopping_admin"
    SHOPPING = "shopping"
    WIKIPEDIA = "wikipedia"
    HOMEPAGE = "homepage"

    @classmethod
    def _missing_(cls, value: Any) -> Self | None:
        # Strip underscores and try to match
        if isinstance(value, str):
            stripped = value.strip("_")
            for member in cls:
                if stripped in (member.value, member.name):
                    return member
        return None

    @property
    def url_name_template(self) -> str:
        """The name that appears in the URL for this site."""
        return f"__{self.value.upper()}__"


# ============================================================================
# Evaluation Models
# ============================================================================
ExpectedT = TypeVar("ExpectedT")


class BaseEval(BaseModel, Generic[ExpectedT]):
    """Base class for all evaluation validators."""

    expected: ExpectedT

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        use_enum_values=True,
        arbitrary_types_allowed=True,
    )


class AgentResponseEvaluatorCfg(BaseEval[_FinalAgentResponse]):
    """Validates the agent's response structure, performed operation type, status, and retrieved data.

    Checks that the agent returns properly formatted responses with correct operation types
    (retrieve, navigate, mutate), status codes, and expected data values.

    Example:
        ```json
        {
            "evaluator": "AgentResponseEvaluator",
            "ordered": false,
            "results_schema": {"type": "array", "items": {"type": "string"}},
            "expected": {
                "task_type": "retrieve",
                "status": "SUCCESS",
                "retrieved_data": ["Product Name"]
            }
        }
        ```
    """

    evaluator: Literal["AgentResponseEvaluator"] = "AgentResponseEvaluator"

    ordered: bool = False
    """Whether the retrieved data must match the expected order."""

    results_schema: SerializableMappingProxyType
    """JSON schema defining the structure of the retrieved data array."""


class NetworkEventSpec(BaseModel):
    """Network event validation criteria.

    All fields in the expected block are validated against matching network events.

    Example (basic):
        ```json
        {
            "url": "__SHOPPING_ADMIN__/mui/index/render/?namespace=sales_order_grid",
            "headers": {
                "referer": "__SHOPPING_ADMIN__/sales/order/",
                "X-Requested-With": "XMLHttpRequest"
            },
            "query_string": {"namespace": "sales_order_grid", "filters[status]": "processing"},
            "response_status": 200,
            "http_method": "GET"
        }
        ```

    Example (with JSONPath in post_data):
        ```json
        {
            "url": "__GITLAB__/notes",
            "http_method": "POST",
            "post_data": {
                "$.note.note": "lgtm",
                "$.note.noteable_type": "MergeRequest"
            },
            "response_status": 200
        }
        ```

    Example (hybrid - regular + JSONPath keys):
        ```json
        {
            "url": "__GITLAB__/api/update",
            "http_method": "POST",
            "post_data": {
                "user_id": "123",
                "$.metadata.timestamp": "2024-01-01"
            },
            "response_status": 200
        }
        ```
    """

    url: NonEmptyStr | list[NonEmptyStr]
    """URL to search for and validate in network events (required)."""

    headers: SerializableMappingProxyType | None = None
    """Optional request headers to match and validate (case-insensitive names, exact values)."""

    query_params: QueryParams | None = None
    """Optional query parameters to validate in the network request."""

    post_data: SerializableMappingProxyType | None = None
    """Optional POST data to validate in the network request.

    Supports JSONPath expressions for extracting values from nested structures.
    Keys starting with '$' are treated as JSONPath expressions.
    Can mix regular top-level keys with JSONPath keys in the same dict.

    Examples:
        Regular keys: {"user_id": "123", "action": "update"}
        JSONPath keys: {"$.note.note": "lgtm", "$.note.noteable_type": "MergeRequest"}
        Hybrid: {"user_id": "123", "$.metadata.timestamp": "2024-01-01"}
    """

    response_content: SerializableMappingProxyType | None = None
    """Optional response content to validate in the network response.

    Supports JSONPath expressions for extracting values from nested structures.
    Keys starting with '$' are treated as JSONPath expressions.

    Examples:
        Regular keys: {"status": "success"}
        JSONPath keys: {"$.data.user.name": "Alice", "$.data.status": "success"}
    """

    response_status: int = 200
    """Expected HTTP status code (default: 200)."""

    http_method: str = "GET"
    """Expected HTTP method (default: GET for navigation events)."""

    response_cookies: SerializableMappingProxyType | None = None
    """Optional response cookies to validate in the network response.

    Cookie values are URL-decoded automatically for pattern matching.
    Supports regex patterns via NormalizedString (case-insensitive).

    Example:
        {"mage-messages": "^.*toothpaste.* has been added to your wish list.*$"}
    """


class NetworkEventEvaluatorCfg(BaseEval[NetworkEventSpec]):
    """Validates network events by checking URL, headers, query params, status, event type, and method.

    Searches for network events matching the expected criteria and validates all fields
    in the expected block. Provides a cleaner API where all validation criteria are
    grouped under 'expected'.

    Example:
        ```json
        {
            "evaluator": "NetworkEventEvaluator",
            "site": "shopping_admin",
            "url_match_mode": "prefix",
            "last_event_only": true,
            "ignored_query_params_patterns": ["^paging", "^sorting", "isAjax"],
            "expected": {
                "url": "__SHOPPING_ADMIN__/mui/index/render/?namespace=sales_order_grid",
                "headers": {
                    "referer": "__SHOPPING_ADMIN__/sales/order/",
                    "X-Requested-With": "XMLHttpRequest"
                },
                "query_string": {
                    "namespace": "sales_order_grid",
                    "filters[status]": "processing"
                },
                "post_data": {
                    "report_type": "created_at_order",
                    "from": "02/1/2023"
                },
                "response_status": 200,
                "http_method": "GET"
            }
        }
        ```
    """

    evaluator: Literal["NetworkEventEvaluator"] = "NetworkEventEvaluator"

    last_event_only: bool = True
    """If True, validate only the last matching event. If False, validate if ANY event matches."""

    ignored_query_params: tuple[str, ...] | None = None
    """Query parameter names to ignore during comparison (literal matching)."""

    ignored_query_params_patterns: tuple[str, ...] | None = None
    """Regex patterns for query parameter names to ignore during comparison (case-sensitive)."""

    decode_base64_query: bool = False
    """If True, decode base64-encoded query strings from URL path before comparison."""

    query_params_schema: SerializableMappingProxyType | None = None
    """Optional JSON schema for type-aware query parameter comparison (e.g., dates, currency)."""

    post_data_schema: SerializableMappingProxyType | None = None
    """Optional JSON schema for type-aware post_data comparison (e.g., dates, currency)."""

    ignored_post_data_params_patterns: tuple[str, ...] | None = None
    """Regex patterns for POST data parameter names to ignore during comparison (case-sensitive)."""

    should_not_exist: bool = False
    """If True, validation succeeds when NO matching events are found (inverts default behavior)."""


EvaluatorCfg = Annotated[
    AgentResponseEvaluatorCfg | NetworkEventEvaluatorCfg,
    Field(discriminator="evaluator"),
]


# ============================================================================
# Task Model
# ============================================================================
class WebArenaVerifiedTask(BaseModel):
    """Pydantic model for a WebArena Verified task."""

    sites: tuple[WebArenaSite, ...]
    """List of platforms involved (e.g., gitlab, shopping_admin)."""

    task_id: int
    """Unique identifier for the task."""

    intent_template_id: int
    """Groups tasks from the same template."""

    start_urls: tuple[NonEmptyStr, ...]
    """Initial URLs where the task begins."""

    intent: NonEmptyStr
    """Natural language description of what to accomplish."""

    eval: tuple[EvaluatorCfg, ...]
    """Array of evaluator configurations."""

    intent_template: NonEmptyStr
    """Template with placeholders (e.g., 'Get top-{{n}} products')."""

    instantiation_dict: SerializableMappingProxyType
    """Values used to fill template placeholders."""

    revision: Annotated[int, Field(ge=1)]
    """Integer revision number tracking task changes (minimum 1)."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    @model_validator(mode="after")
    def check_eval_has_agent_response(self) -> Self:
        """Validate that eval contains at least one AgentResponseEval item."""
        if not any(isinstance(item, AgentResponseEvaluatorCfg) for item in self.eval):
            raise ValueError("eval must contain at least one AgentResponseEval item")
        return self

    @property
    def expected_agent_response(self) -> FinalAgentResponse:
        """Return the expected agent response from the first AgentResponseEval."""
        for item in self.eval:
            if isinstance(item, AgentResponseEvaluatorCfg):
                return item.expected
        raise ValueError("No AgentResponseEval found in eval")

    @property
    def expected_action(self) -> str:
        """Return the expected task type from the expected agent response."""
        return self.expected_agent_response.task_type

    @property
    def network_event_evaluator_cfgs(self) -> tuple[NetworkEventEvaluatorCfg, ...]:
        """Return all NetworkEventEvaluatorCfg items in eval."""
        return tuple(item for item in self.eval if isinstance(item, NetworkEventEvaluatorCfg))

    @property
    def is_navigate_task(self) -> bool:
        """Check if this is a navigate task."""
        return self.expected_agent_response.is_navigate

    @property
    def is_mutate_task(self) -> bool:
        """Check if this is a mutate task."""
        return self.expected_agent_response.is_mutate

    @property
    def is_retrieve_task(self) -> bool:
        """Check if this is a retrieve task."""
        return self.expected_agent_response.is_retrieve

    @property
    def sites_str(self) -> str:
        """Return a comma-separated string of site names."""
        return "-".join(sorted([site.value for site in self.sites]))

    def __str__(self) -> str:
        """Pretty print task with key information."""
        return (
            f"WebArenaVerifiedTask(\n"
            f"  task_id={self.task_id},\n"
            f"  intent_template_id={self.intent_template_id},\n"
            f"  sites={list(self.sites)},\n"
            f"  intent={self.intent!r},\n"
            f"  start_urls={list(self.start_urls)},\n"
            f")"
        )

    def __repr__(self) -> str:
        """Repr with key information."""
        return (
            f"WebArenaVerifiedTask(task_id={self.task_id}, "
            f"intent_template_id={self.intent_template_id}, sites=[{self.sites_str}])"
        )
```

## Raw Source Provenance

```json
{
  "benchmark_version": "v1.2.3",
  "case_unit_id": "224",
  "controller_runtime_files": [
    "case_packet.json"
  ],
  "copied_files": [
    "derived/tag_task.json",
    "derived/task.json",
    "official/LICENSE",
    "official/src/webarena_verified/api/internal/evaluator.py",
    "official/src/webarena_verified/core/evaluation/evaluators/agent_response_evaluator.py",
    "official/src/webarena_verified/core/evaluation/evaluators/base.py",
    "official/src/webarena_verified/core/evaluation/value_comparator.py",
    "official/src/webarena_verified/core/evaluation/value_normalizer.py",
    "official/src/webarena_verified/types/agent_response.py",
    "official/src/webarena_verified/types/eval.py",
    "official/src/webarena_verified/types/task.py"
  ],
  "derived_files": [
    "derived/task.json",
    "derived/tag_task.json"
  ],
  "domain": "webarena_verified",
  "drafter_reviewer_only_files": [
    "case_packet.md",
    "raw_case_manifest.json",
    "raw_case/**"
  ],
  "evaluator_names_in_order": [
    "AgentResponseEvaluator"
  ],
  "file_sources": {
    "derived/tag_task.json": "experiments/official_splits/webarena_verified_v1_2_3_source/assets/dataset/webarena-verified.json#task_id=224",
    "derived/task.json": "experiments/official_splits/webarena_verified_official_812.json#task_id=224",
    "official/LICENSE": "https://github.com/ServiceNow/webarena-verified.git@6473f72db5dcefc97b5725b59e734504edc28a21/LICENSE",
    "official/src/webarena_verified/api/internal/evaluator.py": "https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/api/internal/evaluator.py",
    "official/src/webarena_verified/core/evaluation/evaluators/agent_response_evaluator.py": "https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/core/evaluation/evaluators/agent_response_evaluator.py",
    "official/src/webarena_verified/core/evaluation/evaluators/base.py": "https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/core/evaluation/evaluators/base.py",
    "official/src/webarena_verified/core/evaluation/value_comparator.py": "https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/core/evaluation/value_comparator.py",
    "official/src/webarena_verified/core/evaluation/value_normalizer.py": "https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/core/evaluation/value_normalizer.py",
    "official/src/webarena_verified/types/agent_response.py": "https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/types/agent_response.py",
    "official/src/webarena_verified/types/eval.py": "https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/types/eval.py",
    "official/src/webarena_verified/types/task.py": "https://github.com/ServiceNow/webarena-verified.git/blob/6473f72db5dcefc97b5725b59e734504edc28a21/src/webarena_verified/types/task.py"
  },
  "model_visible_files": [
    "agent_input.json"
  ],
  "normalized_source_path": "experiments/official_splits/webarena_verified_official_812.json",
  "normalized_source_sha256": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f",
  "normalized_source_task_canonical_sha256": "4011762dec8d2d64ced41cafa8462a7132369fc867591a9a50d827d9a77c745d",
  "official_commit": "6473f72db5dcefc97b5725b59e734504edc28a21",
  "official_evaluator_checksum": "35c3385b1db4b3378657589f95f50defd4234bd36e5b93d44733fd561b01db4e",
  "official_files": [
    "official/LICENSE",
    "official/src/webarena_verified/api/internal/evaluator.py",
    "official/src/webarena_verified/core/evaluation/evaluators/agent_response_evaluator.py",
    "official/src/webarena_verified/core/evaluation/evaluators/base.py",
    "official/src/webarena_verified/core/evaluation/value_comparator.py",
    "official/src/webarena_verified/core/evaluation/value_normalizer.py",
    "official/src/webarena_verified/types/agent_response.py",
    "official/src/webarena_verified/types/eval.py",
    "official/src/webarena_verified/types/task.py"
  ],
  "official_tag_dataset_path": "experiments/official_splits/webarena_verified_v1_2_3_source/assets/dataset/webarena-verified.json",
  "official_tag_dataset_sha256": "d65275660814663375028e9017e1f929e3c38321041b125795e2713b52243d30",
  "official_tag_task_canonical_sha256": "a0777a1cf32ec717f86a7bd712d79a61ba63f68588651bf1ae580c473e6e70a2",
  "packet_files": [
    "derived/task.json",
    "derived/tag_task.json",
    "official/src/webarena_verified/api/internal/evaluator.py",
    "official/src/webarena_verified/core/evaluation/evaluators/base.py",
    "official/src/webarena_verified/core/evaluation/evaluators/agent_response_evaluator.py",
    "official/src/webarena_verified/core/evaluation/value_comparator.py",
    "official/src/webarena_verified/core/evaluation/value_normalizer.py",
    "official/src/webarena_verified/types/agent_response.py",
    "official/src/webarena_verified/types/eval.py",
    "official/src/webarena_verified/types/task.py"
  ],
  "required_run_artifacts": [
    "agent_response.json",
    "network.har"
  ],
  "schema_version": "webarena_verified_raw_case_manifest/v2",
  "sha256_per_file": {
    "derived/tag_task.json": "dca3728dbbdbe2e0b2f8577fb628278cc8f1cf837b98af2bf891f3b1b16048d1",
    "derived/task.json": "e6ba5ba0e6f3ab7072915d63908c0645fdf83b258c3ad36f111e164c0b4beb99",
    "official/LICENSE": "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4",
    "official/src/webarena_verified/api/internal/evaluator.py": "e4d390700985a5921e6a86d1782a4c9803c85728b38a6cfd16ad6e9aebaec714",
    "official/src/webarena_verified/core/evaluation/evaluators/agent_response_evaluator.py": "8ae2caf59c6fafecf4ec259ea67bf79d27f19c7fcbdc33a312cea730c4e54c31",
    "official/src/webarena_verified/core/evaluation/evaluators/base.py": "56c5d1db9554690e7fac76f2b1690a8c424ed0931d71dd260639eca99f2a542a",
    "official/src/webarena_verified/core/evaluation/value_comparator.py": "330d6e999e80e45a47ae569cf26c2d32459b17ab93383b6dd1d7676fe2c0257b",
    "official/src/webarena_verified/core/evaluation/value_normalizer.py": "3ad6bf5a3f9630714fea69943aede7e616d2fc9926264e590aacbd4498d41b62",
    "official/src/webarena_verified/types/agent_response.py": "d37b9bee08f4be98cd2567d03193579c194c74828a2c9d8b13dab9b5e6bc1ee7",
    "official/src/webarena_verified/types/eval.py": "f9c2a2aa4fcc839232f3cab88c9618b601c050e2d46b97630f96664257e95140",
    "official/src/webarena_verified/types/task.py": "ec44b655318fc3e25152abd2844b7a0e3b0ea860132886f69b79e39785b401f5"
  },
  "source_refs": [
    "experiments/official_splits/webarena_verified_official_812.json#task_id=224",
    "experiments/official_splits/webarena_verified_v1_2_3_source/assets/dataset/webarena-verified.json#task_id=224"
  ],
  "source_sha256": "10752f67cb4652831da85419925863cc5315db9c53bae42370046b70f032484f",
  "source_task_sha256": "4011762dec8d2d64ced41cafa8462a7132369fc867591a9a50d827d9a77c745d",
  "task_id": "224",
  "task_score_composition": "all_evaluator_scores_must_equal_1.0",
  "top_level_file_sha256": {
    "agent_input.json": "1fdab589dfc3983efa8a3764f358153668478d697f418b182a162626aab51195",
    "case_packet.json": "ac5043fac9e783fc6639b2b2408979fc8fda250fbee7e71378a82736b71dd3fa"
  }
}
```
