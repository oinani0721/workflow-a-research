# Tests for differentiated remediation strategy injection in question generation
# Sub-task 2: question_generator.py should consume error types from layer4_rules.md
#
# layer4_rules.md defines 4 error types with distinct strategies:
#   - 破题错误 -> "同结构不同包装" verification questions
#   - 推理谬误 -> error-finding / counterexample questions
#   - 知识点缺失 -> fallback to definition-level questions
#   - 似懂非懂 -> discrimination / transfer questions
#
# The ACP error_history contains error_type per error.
# build_5_layer_prompt should inject the matching strategy into the prompt.
"""
TDD RED phase: Tests for remediation strategy selection and injection.

get_dominant_error_type(): Analyze error_history to find the most frequent type.
get_remediation_directive(): Map error type to concrete prompt directive.
build_5_layer_prompt(): Verify the prompt includes error-type-specific directives.
"""

import pytest

from app.models.exam_models import ACPData, ExamMode


class TestGetDominantErrorType:
    """Tests for determining the dominant error type from ACP error_history."""

    def test_single_error_returns_its_type(self):
        """One error record -> that error type is dominant."""
        from app.services.question_generator import get_dominant_error_type

        errors = [{"error_type": "破题错误", "description": "failed to parse"}]
        assert get_dominant_error_type(errors) == "破题错误"

    def test_majority_type_wins(self):
        """Most frequent error type is selected."""
        from app.services.question_generator import get_dominant_error_type

        errors = [
            {"error_type": "推理谬误", "description": "logic gap"},
            {"error_type": "推理谬误", "description": "false cause"},
            {"error_type": "知识点缺失", "description": "missing def"},
        ]
        assert get_dominant_error_type(errors) == "推理谬误"

    def test_empty_errors_returns_none(self):
        """No errors -> None (no specific strategy needed)."""
        from app.services.question_generator import get_dominant_error_type

        assert get_dominant_error_type([]) is None

    def test_unknown_type_falls_through(self):
        """Unknown error types still get returned as dominant."""
        from app.services.question_generator import get_dominant_error_type

        errors = [{"error_type": "other_type", "description": "something"}]
        assert get_dominant_error_type(errors) == "other_type"

    def test_tie_returns_first_encountered(self):
        """When two types tie, return the one encountered first."""
        from app.services.question_generator import get_dominant_error_type

        errors = [
            {"error_type": "破题错误", "description": "a"},
            {"error_type": "知识点缺失", "description": "b"},
        ]
        result = get_dominant_error_type(errors)
        assert result in ("破题错误", "知识点缺失")


class TestGetRemediationDirective:
    """Tests for mapping error type to prompt directive text."""

    def test_poti_error_produces_structure_directive(self):
        """破题错误 -> directive mentioning '同结构不同包装' or structure variation."""
        from app.services.question_generator import get_remediation_directive

        directive = get_remediation_directive("破题错误")
        assert "同结构" in directive or "破题" in directive, (
            f"破题错误 directive should mention structure variation, got: {directive}"
        )

    def test_reasoning_error_produces_fallacy_directive(self):
        """推理谬误 -> directive mentioning error-finding or counterexample."""
        from app.services.question_generator import get_remediation_directive

        directive = get_remediation_directive("推理谬误")
        assert "推理" in directive or "找错" in directive or "反例" in directive, (
            f"推理谬误 directive should mention reasoning/error-finding, got: {directive}"
        )

    def test_knowledge_gap_produces_definition_directive(self):
        """知识点缺失 -> directive mentioning definition or 回退到基础."""
        from app.services.question_generator import get_remediation_directive

        directive = get_remediation_directive("知识点缺失")
        assert "定义" in directive or "基础" in directive or "知识点" in directive, (
            f"知识点缺失 directive should mention definition/basics, got: {directive}"
        )

    def test_superficial_understanding_produces_discrimination_directive(self):
        """似懂非懂 -> directive mentioning 辨析/反例/迁移."""
        from app.services.question_generator import get_remediation_directive

        directive = get_remediation_directive("似懂非懂")
        assert "辨析" in directive or "反例" in directive or "迁移" in directive, (
            f"似懂非懂 directive should mention discrimination/transfer, got: {directive}"
        )

    def test_none_returns_empty_string(self):
        """No error type -> empty directive (no remediation needed)."""
        from app.services.question_generator import get_remediation_directive

        assert get_remediation_directive(None) == ""

    def test_unknown_type_returns_empty_string(self):
        """Unknown error type -> empty directive (graceful fallback)."""
        from app.services.question_generator import get_remediation_directive

        assert get_remediation_directive("completely_unknown_type") == ""

    def test_all_four_types_produce_different_directives(self):
        """Each of the 4 MathCCS error types produces a distinct directive."""
        from app.services.question_generator import get_remediation_directive

        types = ["破题错误", "推理谬误", "知识点缺失", "似懂非懂"]
        directives = [get_remediation_directive(t) for t in types]

        # All should be non-empty
        for t, d in zip(types, directives):
            assert len(d) > 0, f"Error type '{t}' produced empty directive"

        # All should be distinct
        assert len(set(directives)) == 4, (
            f"Expected 4 distinct directives, got {len(set(directives))}: {directives}"
        )


class TestBuildPromptWithRemediation:
    """Tests that build_5_layer_prompt injects a dynamic remediation section.

    The key marker is "### 补救策略指令" which is injected dynamically
    based on error_history, NOT part of the static layer4_rules.md.
    """

    def _make_acp_with_errors(self, error_type: str, count: int = 2) -> ACPData:
        """Create an ACP with error_history of one type."""
        return ACPData(
            node_id="test-node-001",
            node_content="微积分基本定理",
            error_history=[
                {"error_type": error_type, "description": f"error {i}"}
                for i in range(count)
            ],
            effective_proficiency=0.3,
            p_mastery=0.3,
            mastery_label="Developing",
        )

    def test_poti_errors_inject_dynamic_remediation_section(self):
        """ACP with 破题错误 -> prompt has '### 补救策略指令' with 破题 content."""
        from app.services.question_generator import QuestionGenerator

        gen = QuestionGenerator()
        acp = self._make_acp_with_errors("破题错误")
        prompt = gen.build_5_layer_prompt(acp, ExamMode.COMPREHENSIVE)
        assert "### 补救策略指令" in prompt, (
            "Prompt must contain dynamic remediation section header"
        )
        # Find the remediation section and check its content
        idx = prompt.index("### 补救策略指令")
        section = prompt[idx:idx + 200]
        assert "同结构" in section or "破题" in section, (
            f"Remediation section should reference 破题 strategy, got: {section}"
        )

    def test_reasoning_errors_inject_dynamic_remediation_section(self):
        """ACP with 推理谬误 -> dynamic remediation section with reasoning content."""
        from app.services.question_generator import QuestionGenerator

        gen = QuestionGenerator()
        acp = self._make_acp_with_errors("推理谬误")
        prompt = gen.build_5_layer_prompt(acp, ExamMode.COMPREHENSIVE)
        assert "### 补救策略指令" in prompt
        idx = prompt.index("### 补救策略指令")
        section = prompt[idx:idx + 200]
        assert "错误推理" in section or "找错" in section or "反例" in section, (
            f"Remediation section should reference 推理谬误 strategy, got: {section}"
        )

    def test_knowledge_gap_injects_dynamic_remediation_section(self):
        """ACP with 知识点缺失 -> dynamic remediation section with definition content."""
        from app.services.question_generator import QuestionGenerator

        gen = QuestionGenerator()
        acp = self._make_acp_with_errors("知识点缺失")
        prompt = gen.build_5_layer_prompt(acp, ExamMode.COMPREHENSIVE)
        assert "### 补救策略指令" in prompt
        idx = prompt.index("### 补救策略指令")
        section = prompt[idx:idx + 200]
        assert "定义" in section or "基础" in section, (
            f"Remediation section should reference 知识点缺失 strategy, got: {section}"
        )

    def test_superficial_injects_dynamic_remediation_section(self):
        """ACP with 似懂非懂 -> dynamic remediation section with discrimination content."""
        from app.services.question_generator import QuestionGenerator

        gen = QuestionGenerator()
        acp = self._make_acp_with_errors("似懂非懂")
        prompt = gen.build_5_layer_prompt(acp, ExamMode.COMPREHENSIVE)
        assert "### 补救策略指令" in prompt
        idx = prompt.index("### 补救策略指令")
        section = prompt[idx:idx + 200]
        assert "辨析" in section or "迁移" in section, (
            f"Remediation section should reference 似懂非懂 strategy, got: {section}"
        )

    def test_no_errors_no_remediation_section(self):
        """ACP with no error_history -> prompt does NOT contain remediation section."""
        from app.services.question_generator import QuestionGenerator

        gen = QuestionGenerator()
        acp = ACPData(
            node_id="test-node-002",
            node_content="线性代数",
            error_history=[],
            effective_proficiency=0.5,
        )
        prompt = gen.build_5_layer_prompt(acp, ExamMode.COMPREHENSIVE)
        assert "### 补救策略指令" not in prompt, (
            "Prompt should not contain remediation section when no errors exist"
        )

    def test_different_error_types_produce_different_prompts(self):
        """Different error types in ACP produce different prompt content."""
        from app.services.question_generator import QuestionGenerator

        gen = QuestionGenerator()
        types = ["破题错误", "推理谬误", "知识点缺失", "似懂非懂"]
        prompts = []
        for error_type in types:
            acp = self._make_acp_with_errors(error_type)
            prompt = gen.build_5_layer_prompt(acp, ExamMode.COMPREHENSIVE)
            prompts.append(prompt)

        # All 4 prompts should be distinct (different remediation directives)
        unique_prompts = set(prompts)
        assert len(unique_prompts) == 4, (
            f"Expected 4 distinct prompts for 4 error types, got {len(unique_prompts)}"
        )
