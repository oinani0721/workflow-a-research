# Tests for differentiated remediation strategy injection into prompts
# Sub-task 2: layer4_rules.md defines 4 error-type strategies but question_generator.py
# does not consume them to produce a targeted directive. These tests verify that
# build_5_layer_prompt injects a *specific* remediation directive based on the dominant
# error type, not just the generic static content from layer4_rules.md.
"""
TDD Red-Green tests for remediation strategy consumption in question_generator.py.

MathCCS 4 error types (from layer4_rules.md):
  - 破题错误 (breakthrough error): "同结构不同包装" strategy
  - 推理谬误 (reasoning fallacy): "找错/反例" strategy
  - 知识点缺失 (knowledge gap): "回退到定义题" strategy
  - 似懂非懂 (partial understanding): "辨析题/反例题/迁移题" strategy

The static layer4 always contains all 4 strategies generically.
The test verifies that a DYNAMIC remediation directive is injected as an explicit
instruction (e.g., "当前补救策略: ...") targeting the student's specific error pattern.
"""

import pytest

from app.models.exam_models import ACPData, ExamMode
from app.services.question_generator import QuestionGenerator


@pytest.fixture
def generator():
    """Create a QuestionGenerator instance (loads prompt templates)."""
    return QuestionGenerator()


def _make_acp(error_type: str, count: int = 2) -> ACPData:
    """Helper: create an ACP with a specific dominant error type."""
    errors = [
        {"error_type": error_type, "description": f"Test error {i}"}
        for i in range(count)
    ]
    return ACPData(
        node_id="test-node-1",
        node_content="微积分基本定理",
        node_type="knowledge_point",
        error_history=errors,
        effective_proficiency=0.3,
        p_mastery=0.3,
        retrievability=0.8,
        mastery_label="Developing",
    )


# The key sentinel: a dynamic directive injected based on error analysis.
# This should NOT be present in the static layer4_rules.md -- it's computed at runtime.
REMEDIATION_DIRECTIVE_MARKER = "当前补救策略"


class TestRemediationStrategyInjection:
    """Verify that build_5_layer_prompt injects a dynamic remediation directive."""

    def test_breakthrough_error_directive(self, generator):
        """破题错误 should produce a directive mentioning '同结构不同包装'."""
        acp = _make_acp("破题错误")
        prompt = generator.build_5_layer_prompt(acp, ExamMode.COMPREHENSIVE)
        assert REMEDIATION_DIRECTIVE_MARKER in prompt, (
            "Expected dynamic remediation directive marker in prompt"
        )
        # The directive should specifically reference the breakthrough error strategy
        # Find the section after the marker
        idx = prompt.index(REMEDIATION_DIRECTIVE_MARKER)
        directive_section = prompt[idx:idx + 200]
        assert "同结构" in directive_section or "不同包装" in directive_section, (
            f"Directive should reference breakthrough error strategy. Got: {directive_section}"
        )

    def test_reasoning_fallacy_directive(self, generator):
        """推理谬误 should produce a directive mentioning '找错' or '反例'."""
        acp = _make_acp("推理谬误")
        prompt = generator.build_5_layer_prompt(acp, ExamMode.COMPREHENSIVE)
        assert REMEDIATION_DIRECTIVE_MARKER in prompt
        idx = prompt.index(REMEDIATION_DIRECTIVE_MARKER)
        directive_section = prompt[idx:idx + 200]
        assert "错误推理" in directive_section or "找错" in directive_section or "反例" in directive_section, (
            f"Directive should reference reasoning fallacy strategy. Got: {directive_section}"
        )

    def test_knowledge_gap_directive(self, generator):
        """知识点缺失 should produce a directive mentioning '定义题' or '回退'."""
        acp = _make_acp("知识点缺失")
        prompt = generator.build_5_layer_prompt(acp, ExamMode.COMPREHENSIVE)
        assert REMEDIATION_DIRECTIVE_MARKER in prompt
        idx = prompt.index(REMEDIATION_DIRECTIVE_MARKER)
        directive_section = prompt[idx:idx + 200]
        assert "定义题" in directive_section or "回退" in directive_section or "确认基础" in directive_section, (
            f"Directive should reference knowledge gap strategy. Got: {directive_section}"
        )

    def test_partial_understanding_directive(self, generator):
        """似懂非懂 should produce a directive mentioning '辨析' or '迁移'."""
        acp = _make_acp("似懂非懂")
        prompt = generator.build_5_layer_prompt(acp, ExamMode.COMPREHENSIVE)
        assert REMEDIATION_DIRECTIVE_MARKER in prompt
        idx = prompt.index(REMEDIATION_DIRECTIVE_MARKER)
        directive_section = prompt[idx:idx + 200]
        assert "辨析" in directive_section or "迁移" in directive_section, (
            f"Directive should reference partial understanding strategy. Got: {directive_section}"
        )

    def test_no_errors_no_directive(self, generator):
        """When error_history is empty, no remediation directive should be injected."""
        acp = ACPData(
            node_id="test-node-1",
            node_content="微积分基本定理",
            error_history=[],
            effective_proficiency=0.5,
            p_mastery=0.5,
            retrievability=0.8,
            mastery_label="Developing",
        )
        prompt = generator.build_5_layer_prompt(acp, ExamMode.COMPREHENSIVE)
        assert REMEDIATION_DIRECTIVE_MARKER not in prompt, (
            "No remediation directive should appear when there are no errors"
        )

    def test_mixed_errors_uses_dominant_type(self, generator):
        """When multiple error types exist, the most frequent one determines strategy."""
        errors = [
            {"error_type": "破题错误", "description": "err1"},
            {"error_type": "推理谬误", "description": "err2"},
            {"error_type": "推理谬误", "description": "err3"},
            {"error_type": "推理谬误", "description": "err4"},
        ]
        acp = ACPData(
            node_id="test-node-1",
            node_content="微积分基本定理",
            error_history=errors,
            effective_proficiency=0.3,
            p_mastery=0.3,
            retrievability=0.8,
            mastery_label="Developing",
        )
        prompt = generator.build_5_layer_prompt(acp, ExamMode.COMPREHENSIVE)
        assert REMEDIATION_DIRECTIVE_MARKER in prompt
        idx = prompt.index(REMEDIATION_DIRECTIVE_MARKER)
        directive_section = prompt[idx:idx + 200]
        # Dominant type is 推理谬误 (3 out of 4)
        assert "错误推理" in directive_section or "找错" in directive_section or "反例" in directive_section, (
            f"Should use dominant error type (推理谬误). Got: {directive_section}"
        )
