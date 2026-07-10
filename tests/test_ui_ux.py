"""
Tests for Temuclaude UI/UX Generation Module — Loop Engineering System

Tests all components:
- IntentClassifier: 5 categories, confidence, vagueness detection
- SpecGenerator: Template loading, field filling, complexity estimation
- ModelRouter: Routing strategy for each intent + phase
- MemoryBank: Pattern save/load, similarity search, NOTES.md
- QualityGates: All 10 gates (HTML valid, a11y, responsive, etc.)
- VisualValidator: Static analysis, performance estimation
- IterationController: Loop management, critique generation
- LoopEngine: Full pipeline integration

Run: python -m pytest tests/test_ui_ux.py -v
"""
import asyncio
import os
import sys
import tempfile
import shutil
import pytest

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui_ux import (
    IntentClassifier, Intent,
    SpecGenerator, Spec,
    ModelRouter, ModelChoice,
    MemoryBank, Pattern,
    QualityGates, QualityReport,
    VisualValidator, VisualValidationResult,
    IterationController, LoopSummary,
    LoopEngine, GenerationResult,
)


# ============================================================
# INTENT CLASSIFIER TESTS
# ============================================================

class TestIntentClassifier:
    """Test intent classification for 5 categories."""

    def setup_method(self):
        self.classifier = IntentClassifier()

    def test_game_3d_detection(self):
        """Should detect game/3D prompts."""
        intent = self.classifier.classify("Create a Minecraft-style voxel game in the browser")
        assert intent.category == "game_3d"
        assert intent.confidence > 0
        assert "minecraft" in intent.keywords_matched

    def test_game_3d_physics_keywords(self):
        """Should detect physics/game keywords."""
        intent = self.classifier.classify("Build a 3D first person shooter with physics")
        assert intent.category == "game_3d"
        assert "3d" in intent.keywords_matched or "first person" in intent.keywords_matched

    def test_physics_demo_detection(self):
        """Should detect physics simulation prompts."""
        intent = self.classifier.classify("Create a Verlet cloth simulation with WebGL")
        assert intent.category == "physics_demo"
        assert "verlet" in intent.keywords_matched
        assert "cloth" in intent.keywords_matched

    def test_physics_demo_particle(self):
        """Should detect particle/fluid demos."""
        intent = self.classifier.classify("Build a particle fluid simulation with shaders")
        assert intent.category == "physics_demo"
        assert "particle" in intent.keywords_matched or "fluid" in intent.keywords_matched

    def test_dashboard_detection(self):
        """Should detect dashboard/SaaS prompts."""
        intent = self.classifier.classify("Build an analytics dashboard with charts and tables")
        assert intent.category == "dashboard_saas"
        assert "dashboard" in intent.keywords_matched

    def test_dashboard_admin(self):
        """Should detect admin panel prompts."""
        intent = self.classifier.classify("Create an admin panel for SaaS with KPI metrics")
        assert intent.category == "dashboard_saas"

    def test_landing_page_detection(self):
        """Should detect landing page prompts."""
        intent = self.classifier.classify("Design a landing page with hero, pricing, and testimonials")
        assert intent.category == "landing_page"
        assert "landing" in intent.keywords_matched

    def test_mobile_app_detection(self):
        """Should detect mobile app prompts."""
        intent = self.classifier.classify("Build a mobile app for iOS and Android with React Native")
        assert intent.category == "mobile_app"
        assert "mobile" in intent.keywords_matched or "ios" in intent.keywords_matched

    def test_vague_prompt_detection(self):
        """Should flag vague prompts."""
        intent = self.classifier.classify("make something cool")
        assert intent.is_vague == True

    def test_specific_prompt_not_vague(self):
        """Should not flag specific prompts as vague."""
        intent = self.classifier.classify("Create a Minecraft voxel game with Three.js, first person camera, block placement")
        assert intent.is_vague == False

    def test_default_fallback(self):
        """Should default to landing_page for unrecognized prompts."""
        intent = self.classifier.classify("hello world")
        assert intent.category == "landing_page"
        assert intent.confidence < 0.5

    def test_confidence_increases_with_keywords(self):
        """More keywords should yield higher confidence."""
        intent1 = self.classifier.classify("game")
        intent2 = self.classifier.classify("minecraft voxel 3d game first person physics")
        assert intent2.confidence > intent1.confidence

    def test_all_categories_supported(self):
        """Should support all 5 categories."""
        categories = self.classifier.get_all_categories()
        assert "game_3d" in categories
        assert "physics_demo" in categories
        assert "dashboard_saas" in categories
        assert "landing_page" in categories
        assert "mobile_app" in categories

    def test_needs_clarification_returns_question(self):
        """Should return clarification question for vague prompts."""
        intent = Intent(
            category="game_3d", confidence=0.2, keywords_matched=[],
            spec_template="game_3d_spec.md", stack="three.js", model="glm-5.2",
            is_vague=True, quality_bar="", raw_prompt="make a game"
        )
        question = self.classifier.needs_clarification(intent)
        assert question is not None
        assert "features" in question.lower()

    def test_no_clarification_for_specific_prompt(self):
        """Should not need clarification for specific prompts."""
        intent = Intent(
            category="game_3d", confidence=0.9, keywords_matched=["minecraft"],
            spec_template="game_3d_spec.md", stack="three.js", model="glm-5.2",
            is_vague=False, quality_bar="", raw_prompt="minecraft voxel game"
        )
        question = self.classifier.needs_clarification(intent)
        assert question is None


# ============================================================
# SPEC GENERATOR TESTS
# ============================================================

class TestSpecGenerator:
    """Test spec generation from intents."""

    def setup_method(self):
        self.generator = SpecGenerator()
        self.classifier = IntentClassifier()

    def test_generate_game_spec(self):
        """Should generate game spec from game intent."""
        intent = self.classifier.classify("Create a Minecraft voxel game with physics")
        spec = self.generator.generate(intent)
        assert spec.markdown
        assert "Minecraft" in spec.markdown or "voxel" in spec.markdown.lower()
        assert "Three.js" in spec.markdown or "three.js" in spec.markdown.lower()
        assert spec.estimated_complexity == "complex"

    def test_generate_physics_spec(self):
        """Should generate physics demo spec."""
        intent = self.classifier.classify("Build a Verlet cloth simulation with WebGL")
        spec = self.generator.generate(intent)
        assert spec.markdown
        assert "Verlet" in spec.markdown or "webgl" in spec.markdown.lower()
        assert "raw webgl" in spec.markdown.lower()

    def test_generate_dashboard_spec(self):
        """Should generate dashboard spec."""
        intent = self.classifier.classify("Build an analytics dashboard with charts")
        spec = self.generator.generate(intent)
        assert spec.markdown
        assert "Next.js" in spec.markdown or "shadcn" in spec.markdown.lower()

    def test_generate_landing_spec(self):
        """Should generate landing page spec."""
        intent = self.classifier.classify("Design a landing page with hero and pricing")
        spec = self.generator.generate(intent)
        assert spec.markdown
        assert "hero" in spec.markdown.lower()
        assert "pricing" in spec.markdown.lower()

    def test_generate_mobile_spec(self):
        """Should generate mobile app spec."""
        intent = self.classifier.classify("Build a mobile app for iOS with React Native")
        spec = self.generator.generate(intent)
        assert spec.markdown
        assert "Expo" in spec.markdown or "React Native" in spec.markdown

    def test_spec_has_quality_bar(self):
        """Spec should include the quality bar."""
        intent = self.classifier.classify("Create a Minecraft game")
        spec = self.generator.generate(intent)
        assert "impressive enough to share" in spec.markdown.lower() or "quality bar" in spec.markdown.lower()

    def test_spec_with_user_context(self):
        """Should fill user context fields."""
        intent = self.classifier.classify("Build a landing page")
        spec = self.generator.generate(intent, user_context={
            "colors": "#ff0000, #00ff00, #0000ff",
            "target_audience": "Developers",
            "brand": "AcmeCorp",
        })
        assert "#ff0000" in spec.markdown
        assert "Developers" in spec.markdown
        assert "AcmeCorp" in spec.markdown

    def test_color_extraction_from_prompt(self):
        """Should extract colors from prompt."""
        intent = self.classifier.classify("Create a dark cinematic landing page")
        spec = self.generator.generate(intent)
        assert "dark" in spec.markdown.lower() or "#" in spec.markdown

    def test_complexity_estimation(self):
        """Should estimate complexity correctly."""
        # Short prompt = simple
        intent = self.classifier.classify("Build a landing page")
        spec = self.generator.generate(intent)
        assert spec.estimated_complexity in ("simple", "medium")

        # Game = always complex
        intent = self.classifier.classify("Create a Minecraft voxel game")
        spec = self.generator.generate(intent)
        assert spec.estimated_complexity == "complex"

    def test_token_estimation(self):
        """Should estimate target tokens."""
        intent = self.classifier.classify("Build a dashboard")
        spec = self.generator.generate(intent)
        assert spec.target_tokens > 0
        # Games need more tokens
        game_intent = self.classifier.classify("Create a 3D game")
        game_spec = self.generator.generate(game_intent)
        assert game_spec.target_tokens >= spec.target_tokens

    def test_template_filled(self):
        """All template placeholders should be filled."""
        intent = self.classifier.classify("Build a landing page")
        spec = self.generator.generate(intent)
        # No unfilled placeholders
        assert "{{ " not in spec.markdown
        assert "{{" not in spec.markdown


# ============================================================
# MODEL ROUTER TESTS
# ============================================================

class TestModelRouter:
    """Test model routing for intents and phases."""

    def setup_method(self):
        self.router = ModelRouter()

    def test_route_game_3d(self):
        """Should route complex game generation to the coding escalation role."""
        intent = type("I", (), {"category": "game_3d"})()
        choice = self.router.route(intent, phase="generation")
        assert choice.model == "grok-4.5"
        assert choice.max_tokens >= 12000

    def test_route_physics_demo(self):
        """Should route physics demos to the coding escalation role."""
        intent = type("I", (), {"category": "physics_demo"})()
        choice = self.router.route(intent, phase="generation")
        assert choice.model == "grok-4.5"

    def test_route_dashboard(self):
        """Should route dashboard to precision coding model."""
        intent = type("I", (), {"category": "dashboard_saas"})()
        choice = self.router.route(intent, phase="generation")
        assert choice.model == "deepseek-v4-pro"
        assert choice.temperature <= 0.3  # Low temp for precision

    def test_route_landing_page(self):
        """Should route landing page to creative model."""
        intent = type("I", (), {"category": "landing_page"})()
        choice = self.router.route(intent, phase="generation")
        assert choice.model == "minimax-m3"
        assert choice.temperature >= 0.7  # High temp for creativity

    def test_route_spec_generation(self):
        """Should route spec generation to orchestrator."""
        intent = type("I", (), {"category": "game_3d"})()
        choice = self.router.route(intent, phase="spec_generation")
        assert choice.model == "glm-5.2"
        assert choice.role == "spec"

    def test_route_critique(self):
        """Should route critique to verifier."""
        intent = type("I", (), {"category": "game_3d"})()
        choice = self.router.route(intent, phase="critique")
        assert choice.model == "nemotron-3-ultra"
        assert choice.role == "critique"

    def test_route_refine(self):
        """Should route refine to precision model."""
        intent = type("I", (), {"category": "dashboard_saas"})()
        choice = self.router.route(intent, phase="refine")
        assert choice.model == "deepseek-v4-pro"
        assert choice.role == "refine"

    def test_get_model_for_intent(self):
        """Should return model name for intent category."""
        model = self.router.get_model_for_intent("game_3d")
        assert model == "grok-4.5"
        model = self.router.get_model_for_intent("landing_page")
        assert model == "minimax-m3"

    def test_rationale_provided(self):
        """Should provide rationale for each routing decision."""
        intent = type("I", (), {"category": "game_3d"})()
        choice = self.router.route(intent, phase="generation")
        assert choice.rationale
        assert len(choice.rationale) > 10

    def test_all_strategies_available(self):
        """Should have routing strategies for all intents."""
        strategies = self.router.get_all_strategies()
        assert "game_3d" in strategies
        assert "physics_demo" in strategies
        assert "dashboard_saas" in strategies
        assert "landing_page" in strategies
        assert "mobile_app" in strategies
        assert "spec_generation" in strategies
        assert "critique" in strategies
        assert "refine" in strategies


# ============================================================
# MEMORY BANK TESTS
# ============================================================

class TestMemoryBank:
    """Test memory bank persistence."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.memory = MemoryBank(memory_dir=self.temp_dir)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_load_note(self):
        """Should save and load notes."""
        self.memory.save_note("Test note about game generation", "decision")
        notes = self.memory.load_notes()
        assert "Test note" in notes
        assert "decision" in notes

    def test_save_and_load_pattern(self):
        """Should save and load patterns."""
        pattern = Pattern(
            pattern_id="test123",
            intent_category="game_3d",
            prompt_hash="abc123",
            spec_summary="Minecraft voxel game",
            generation_summary="Three.js voxel engine",
            quality_score=0.92,
            iterations=2,
            techniques_used=["html_valid", "responsive_meta"],
            timestamp="2026-07-06T12:00:00Z",
            success=True,
        )
        self.memory.save_pattern(pattern)
        patterns = self.memory.load_patterns()
        assert "test123" in patterns
        assert patterns["test123"]["quality_score"] == 0.92

    def test_find_similar_patterns(self):
        """Should find patterns by category."""
        # Save multiple patterns
        for i, category in enumerate(["game_3d", "game_3d", "landing_page"]):
            pattern = Pattern(
                pattern_id=f"test{i}",
                intent_category=category,
                prompt_hash=f"hash{i}",
                spec_summary=f"Summary {i}",
                generation_summary=f"Gen {i}",
                quality_score=0.8 + i * 0.05,
                iterations=1,
                techniques_used=["html_valid"],
                timestamp="2026-07-06T12:00:00Z",
                success=True,
            )
            self.memory.save_pattern(pattern)

        # Find game_3d patterns
        similar = self.memory.find_similar_patterns("game_3d")
        assert len(similar) == 2
        # Should be sorted by quality (highest first)
        assert similar[0]["quality_score"] >= similar[1]["quality_score"]

    def test_find_pattern_by_prompt(self):
        """Should find pattern by prompt hash."""
        prompt = "Create a Minecraft game"
        pattern = Pattern(
            pattern_id="test_hash",
            intent_category="game_3d",
            prompt_hash=self.memory._hash_prompt(prompt),
            spec_summary="Voxel game",
            generation_summary="Three.js game",
            quality_score=0.9,
            iterations=1,
            techniques_used=["html_valid"],
            timestamp="2026-07-06T12:00:00Z",
            success=True,
        )
        self.memory.save_pattern(pattern)

        found = self.memory.find_pattern_by_prompt(prompt)
        assert found is not None
        assert found["intent_category"] == "game_3d"

    def test_get_stats(self):
        """Should return memory bank statistics."""
        # Save a few patterns
        for i in range(3):
            pattern = Pattern(
                pattern_id=f"stat{i}",
                intent_category="game_3d" if i < 2 else "landing_page",
                prompt_hash=f"hash{i}",
                spec_summary="Summary",
                generation_summary="Gen",
                quality_score=0.85,
                iterations=1,
                techniques_used=["html_valid"],
                timestamp="2026-07-06T12:00:00Z",
                success=i < 2,  # First 2 successful, 3rd not
            )
            self.memory.save_pattern(pattern)

        stats = self.memory.get_stats()
        assert stats["total_patterns"] == 3
        assert stats["successful_patterns"] == 2
        assert stats["success_rate"] == 66.7
        assert "game_3d" in stats["patterns_by_category"]

    def test_create_pattern_from_result(self):
        """Should create Pattern from generation result."""
        intent = Intent(
            category="game_3d", confidence=0.8, keywords_matched=["minecraft"],
            spec_template="game_3d_spec.md", stack="three.js", model="glm-5.2",
            is_vague=False, quality_bar="impressive", raw_prompt="Create a Minecraft game"
        )
        spec = Spec(
            markdown="# Spec", template_used="game_3d_spec.md",
            fields_filled={}, estimated_complexity="complex", target_tokens=16000
        )
        result = type("R", (), {
            "generated_code": "<html>game</html>",
            "quality_score": 0.9,
            "iterations": 2,
            "techniques_passed": ["html_valid", "responsive_meta"],
            "success": True,
        })()
        pattern = self.memory.create_pattern_from_result(intent, spec, result)
        assert pattern.intent_category == "game_3d"
        assert pattern.quality_score == 0.9
        assert pattern.success == True


# ============================================================
# QUALITY GATES TESTS
# ============================================================

class TestQualityGates:
    """Test all quality gates."""

    def setup_method(self):
        self.gates = QualityGates()

    def test_valid_html_passes(self):
        """Valid HTML should pass all gates."""
        code = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test</title>
    <style>body { color: #333; background: #fff; }</style>
</head>
<body>
    <header><nav><a href="#">Home</a></nav></header>
    <main>
        <section>
            <h1>Hello World</h1>
            <button onclick="alert('hi')">Click Me</button>
            <img src="test.png" alt="Test image">
        </section>
    </main>
    <footer>© 2026</footer>
</body>
</html>"""
        report = self.gates.evaluate(code)
        assert report.overall_passed == True
        assert report.overall_score >= 0.8

    def test_missing_doctype_fails(self):
        """Missing DOCTYPE should fail html_valid gate."""
        code = "<html><head></head><body>Hello</body></html>"
        report = self.gates.evaluate(code)
        html_gate = next(g for g in report.gate_results if g.gate_name == "html_valid")
        assert not html_gate.passed

    def test_placeholder_text_fails(self):
        """Placeholder text should fail no_placeholder gate."""
        code = '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"></head><body><p>Lorem ipsum dolor sit amet</p></body></html>'
        report = self.gates.evaluate(code)
        placeholder_gate = next(g for g in report.gate_results if g.gate_name == "no_placeholder")
        assert not placeholder_gate.passed

    def test_missing_viewport_fails(self):
        """Missing viewport meta should fail responsive_meta gate."""
        code = '<!DOCTYPE html><html><head></head><body>Hello</body></html>'
        report = self.gates.evaluate(code)
        viewport_gate = next(g for g in report.gate_results if g.gate_name == "responsive_meta")
        assert not viewport_gate.passed

    def test_images_without_alt_fail(self):
        """Images without alt text should fail accessibility gate."""
        code = '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"></head><body><img src="test.png"></body></html>'
        report = self.gates.evaluate(code)
        a11y_gate = next(g for g in report.gate_results if g.gate_name == "accessibility_attrs")
        assert not a11y_gate.passed

    def test_images_with_alt_pass(self):
        """Images with alt text should pass accessibility gate."""
        code = '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"></head><body><img src="test.png" alt="Test"></body></html>'
        report = self.gates.evaluate(code)
        a11y_gate = next(g for g in report.gate_results if g.gate_name == "accessibility_attrs")
        assert a11y_gate.passed

    def test_semantic_html_score(self):
        """More semantic elements = higher score."""
        code_with_semantic = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"></head>
<body><header><nav></nav></header><main><section><article></article></section></main><footer></footer></body></html>"""
        code_without = '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"></head><body><div><div><div></div></div></div></body></html>'

        report1 = self.gates.evaluate(code_with_semantic)
        report2 = self.gates.evaluate(code_without)
        sem1 = next(g for g in report1.gate_results if g.gate_name == "semantic_html")
        sem2 = next(g for g in report2.gate_results if g.gate_name == "semantic_html")
        assert sem1.score > sem2.score

    def test_single_file_mode_no_external_deps(self):
        """Single file mode should check for external dependencies."""
        gates = QualityGates(single_file_mode=True)
        code = '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"></head><body><script src="https://cdn.example.com/lib.js"></script></body></html>'
        report = gates.evaluate(code)
        deps_gate = next(g for g in report.gate_results if g.gate_name == "no_external_deps")
        assert not deps_gate.passed

    def test_single_file_mode_no_deps(self):
        """Single file mode with no external deps should pass."""
        gates = QualityGates(single_file_mode=True)
        code = '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"></head><body><script>console.log("hi")</script></body></html>'
        report = gates.evaluate(code)
        deps_gate = next(g for g in report.gate_results if g.gate_name == "no_external_deps")
        assert deps_gate.passed

    def test_interactive_elements_score(self):
        """More interactive elements = higher score."""
        code_with_interactions = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"></head>
<body>
<button onclick="a()">Btn1</button>
<button onclick="b()">Btn2</button>
<input type="text" placeholder="Type">
<a href="#">Link</a>
</body></html>"""
        report = self.gates.evaluate(code_with_interactions)
        interactive_gate = next(g for g in report.gate_results if g.gate_name == "interactive_elements")
        assert interactive_gate.passed

    def test_quality_summary(self):
        """Should generate human-readable summary."""
        code = '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"></head><body><h1>Test</h1></body></html>'
        report = self.gates.evaluate(code)
        summary = self.gates.get_gate_summary(report)
        assert "Quality Score" in summary
        assert "PASS" in summary or "FAIL" in summary

    def test_blocking_issues_identified(self):
        """Should identify blocking vs non-blocking issues."""
        code = '<html><body>TODO: add content</body></html>'
        report = self.gates.evaluate(code)
        assert len(report.blocking_issues) > 0 or len(report.warnings) > 0


# ============================================================
# VISUAL VALIDATOR TESTS
# ============================================================

class TestVisualValidator:
    """Test visual validation."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.validator = VisualValidator(
            screenshots_dir=self.temp_dir + "/screenshots",
            reference_dir=self.temp_dir + "/references",
        )

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_static_render_check_valid(self):
        """Should pass valid HTML."""
        result = asyncio.run(
            self.validator.validate('<!DOCTYPE html><html><head></head><body><h1>Hi</h1></body></html>')
        )
        assert result.rendered_correctly == True

    def test_static_render_check_invalid(self):
        """Should fail invalid HTML."""
        result = asyncio.run(
            self.validator.validate('not html at all')
        )
        assert result.rendered_correctly == False

    def test_accessibility_violations_detected(self):
        """Should detect accessibility issues."""
        code = '<!DOCTYPE html><html><body><img src="test.png"><button></button></body></html>'
        result = asyncio.run(
            self.validator.validate(code)
        )
        assert result.accessibility_violations >= 2  # img no alt + empty button

    def test_performance_estimation(self):
        """Should estimate performance score."""
        code = '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"></head><body><h1>Hi</h1></body></html>'
        result = asyncio.run(
            self.validator.validate(code)
        )
        assert result.performance_score is not None
        assert 0 <= result.performance_score <= 100

    def test_cls_estimation(self):
        """Should estimate CLS score."""
        code = '<!DOCTYPE html><html><body><img src="test.png"></body></html>'
        result = asyncio.run(
            self.validator.validate(code)
        )
        assert result.cls_score is not None
        assert result.cls_score >= 0

    def test_lcp_estimation(self):
        """Should estimate LCP."""
        code = '<!DOCTYPE html><html><body><h1>Hi</h1></body></html>'
        result = asyncio.run(
            self.validator.validate(code)
        )
        assert result.lcp_score is not None
        assert result.lcp_score > 0

    def test_warnings_collected(self):
        """Should collect warnings."""
        code = '<!DOCTYPE html><html><body><img src="test.png"></body></html>'
        result = asyncio.run(
            self.validator.validate(code)
        )
        # Should have some warnings (Playwright not installed, a11y issues)
        assert isinstance(result.warnings, list)


# ============================================================
# ITERATION CONTROLLER TESTS
# ============================================================

class TestIterationController:
    """Test the iteration loop."""

    def test_loop_passes_on_first_iteration(self):
        """Should stop if quality threshold met on first try."""
        async def generate_fn(spec, iteration, feedback):
            return '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"></head><body><header><nav><a href="#">Home</a></nav></header><main><section><h1>Hello</h1><button onclick="a()">Click</button><img src="x.png" alt="Test"></section></main><footer>©</footer></body></html>'

        async def validate_fn(code, category):
            gates = QualityGates()
            report = gates.evaluate(code)
            visual = VisualValidationResult(
                screenshots_captured=0, accessibility_violations=0,
                performance_score=90, cls_score=0.05, lcp_score=1.5,
                pixel_diff=None, rendered_correctly=True, errors=[], warnings=[]
            )
            return (report, visual)

        controller = IterationController(max_iterations=3, quality_threshold=0.5)
        summary = asyncio.run(
            controller.run_loop("# Test Spec", generate_fn, validate_fn)
        )
        assert summary.total_iterations == 1
        assert summary.stop_reason == "quality_threshold_met"

    def test_loop_iterates_on_failure(self):
        """Should iterate if quality threshold not met."""
        call_count = [0]

        async def generate_fn(spec, iteration, feedback):
            call_count[0] += 1
            if iteration == 1:
                return '<html><body>TODO</body></html>'  # Bad
            else:
                return '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"></head><body><header><nav><a href="#">Home</a></nav></header><main><section><h1>Hello</h1><button onclick="a()">Click</button><img src="x.png" alt="Test"></section></main><footer>©</footer></body></html>'  # Good

        async def validate_fn(code, category):
            gates = QualityGates()
            report = gates.evaluate(code)
            visual = VisualValidationResult(
                screenshots_captured=0, accessibility_violations=0,
                performance_score=90, cls_score=0.05, lcp_score=1.5,
                pixel_diff=None, rendered_correctly=True, errors=[], warnings=[]
            )
            return (report, visual)

        controller = IterationController(max_iterations=3, quality_threshold=0.8)
        summary = asyncio.run(
            controller.run_loop("# Test Spec", generate_fn, validate_fn)
        )
        assert summary.total_iterations >= 1
        assert call_count[0] >= 1

    def test_loop_max_iterations(self):
        """Should stop at max_iterations if quality never met."""
        async def generate_fn(spec, iteration, feedback):
            return '<html><body>TODO placeholder</body></html>'  # Always bad

        async def validate_fn(code, category):
            gates = QualityGates()
            report = gates.evaluate(code)
            visual = VisualValidationResult(
                screenshots_captured=0, accessibility_violations=0,
                performance_score=50, cls_score=0.2, lcp_score=3.0,
                pixel_diff=None, rendered_correctly=True, errors=[], warnings=[]
            )
            return (report, visual)

        controller = IterationController(max_iterations=2, quality_threshold=0.9)
        summary = asyncio.run(
            controller.run_loop("# Test", generate_fn, validate_fn)
        )
        assert summary.total_iterations == 2
        assert summary.stop_reason == "max_iterations_reached"

    def test_default_critique_generated(self):
        """Should generate critique from quality report."""
        controller = IterationController()
        gates = QualityGates()
        report = gates.evaluate('<html><body>TODO</body></html>')
        visual = VisualValidationResult(
            screenshots_captured=0, accessibility_violations=1,
            performance_score=70, cls_score=0.2, lcp_score=3.0,
            pixel_diff=None, rendered_correctly=False, errors=["error"], warnings=[]
        )
        critique = controller._generate_default_critique(report, visual)
        assert "ISSUES" in critique
        assert "BLOCKING" in critique or "WARNING" in critique

    def test_summary_text(self):
        """Should generate summary text."""
        async def generate_fn(spec, iteration, feedback):
            return '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"></head><body><h1>Test</h1></body></html>'

        async def validate_fn(code, category):
            gates = QualityGates()
            report = gates.evaluate(code)
            visual = VisualValidationResult(
                screenshots_captured=0, accessibility_violations=0,
                performance_score=90, cls_score=0.05, lcp_score=1.5,
                pixel_diff=None, rendered_correctly=True, errors=[], warnings=[]
            )
            return (report, visual)

        controller = IterationController(max_iterations=2, quality_threshold=0.3)
        summary = asyncio.run(
            controller.run_loop("# Test", generate_fn, validate_fn)
        )
        text = controller.get_summary_text(summary)
        assert "Loop Summary" in text
        assert "Iterations" in text


# ============================================================
# LOOP ENGINE TESTS
# ============================================================

class TestLoopEngine:
    """Test the full loop engine."""

    def test_generate_without_model_returns_spec(self):
        """Without a model function, should return the spec."""
        temp_dir = tempfile.mkdtemp()
        try:
            engine = LoopEngine(memory_dir=temp_dir)
            result = asyncio.run(
                engine.generate("Create a Minecraft voxel game")
            )
            assert result.success == True
            assert result.intent.category == "game_3d"
            assert result.spec is not None
            assert "voxel" in result.spec.markdown.lower() or "minecraft" in result.spec.markdown.lower()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_generate_with_mock_model(self):
        """Should run full loop with mock model."""
        async def mock_model(model_name, messages, max_tokens=8000):
            return '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Test</title><style>body{color:#333;background:#fff}</style></head><body><header><nav><a href="#">Home</a></nav></header><main><section><h1>Hello World</h1><button onclick="a()">Click</button><img src="x.png" alt="Test"></section></main><footer>© 2026</footer></body></html>'

        temp_dir = tempfile.mkdtemp()
        try:
            engine = LoopEngine(call_model_fn=mock_model, max_iterations=2, quality_threshold=0.5, memory_dir=temp_dir)
            result = asyncio.run(
                engine.generate("Create a landing page with hero and pricing")
            )
            assert result.intent.category == "landing_page"
            assert result.final_code
            assert result.quality_score >= 0
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_generate_summary(self):
        """Should produce readable summary."""
        temp_dir = tempfile.mkdtemp()
        try:
            engine = LoopEngine(memory_dir=temp_dir)
            result = asyncio.run(
                engine.generate("Create a physics cloth simulation")
            )
            summary = engine.get_summary(result)
            assert "Generation Summary" in summary
            assert "Intent" in summary
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_memory_persistence(self):
        """Patterns should persist across generations."""
        async def mock_model(model_name, messages, max_tokens=8000):
            return '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"></head><body><header><nav><a href="#">H</a></nav></header><main><section><h1>Hi</h1><button>B</button><img alt="x" src="x.png"></section></main><footer>©</footer></body></html>'

        temp_dir = tempfile.mkdtemp()
        try:
            engine = LoopEngine(call_model_fn=mock_model, max_iterations=1, quality_threshold=0.3, memory_dir=temp_dir)
            # First generation
            asyncio.run(
                engine.generate("Create a landing page")
            )
            # Check pattern saved
            memory = MemoryBank(memory_dir=temp_dir)
            patterns = memory.load_patterns()
            assert len(patterns) > 0

            # Second generation should find similar patterns
            similar = memory.find_similar_patterns("landing_page")
            assert len(similar) > 0
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_error_handling(self):
        """Should handle errors gracefully."""
        async def failing_model(model_name, messages, max_tokens=8000):
            raise Exception("Model failed")

        temp_dir = tempfile.mkdtemp()
        try:
            engine = LoopEngine(call_model_fn=failing_model, max_iterations=1, memory_dir=temp_dir)
            result = asyncio.run(
                engine.generate("Create a game")
            )
            assert result.success == False
            assert result.error is not None
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================
# INTEGRATION TEST
# ============================================================

class TestIntegration:
    """Integration tests for the full system."""

    def test_full_pipeline_game_3d(self):
        """Full pipeline: prompt -> intent -> spec -> (mock) generate -> validate."""
        classifier = IntentClassifier()
        generator = SpecGenerator()
        router = ModelRouter()
        gates = QualityGates()

        # Step 1: Classify
        intent = classifier.classify("Create a Minecraft-style voxel game with physics and first-person camera")
        assert intent.category == "game_3d"

        # Step 2: Generate spec
        spec = generator.generate(intent)
        assert "voxel" in spec.markdown.lower() or "minecraft" in spec.markdown.lower()
        assert "Three.js" in spec.markdown or "three.js" in spec.markdown.lower()

        # Step 3: Route model
        choice = router.route(intent, phase="generation")
        assert choice.model == "grok-4.5"

        # Step 4: Validate a sample output
        sample_code = '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width"></head><body><header><nav><a href="#">Menu</a></nav></header><main><section><canvas id="game"></canvas><button>Play</button></section></main><footer>©</footer></body></html>'
        report = gates.evaluate(sample_code)
        assert report.overall_score > 0

    def test_full_pipeline_dashboard(self):
        """Full pipeline for dashboard."""
        classifier = IntentClassifier()
        generator = SpecGenerator()
        router = ModelRouter()

        intent = classifier.classify("Build an analytics dashboard with charts, tables, and KPI metrics")
        assert intent.category == "dashboard_saas"

        spec = generator.generate(intent)
        assert "Next.js" in spec.markdown or "shadcn" in spec.markdown.lower()
        assert "chart" in spec.markdown.lower()

        choice = router.route(intent, phase="generation")
        assert choice.model == "deepseek-v4-pro"

    def test_full_pipeline_physics_demo(self):
        """Full pipeline for physics demo."""
        classifier = IntentClassifier()
        generator = SpecGenerator()
        router = ModelRouter()

        intent = classifier.classify("Create a Verlet cloth simulation with WebGL2, wind forces, mouse interaction")
        assert intent.category == "physics_demo"

        spec = generator.generate(intent)
        assert "Verlet" in spec.markdown
        assert "WebGL" in spec.markdown
        assert "raw webgl" in spec.markdown.lower()

        choice = router.route(intent, phase="generation")
        assert choice.model == "grok-4.5"

    def test_three_layer_stack(self):
        """Test the three-layer engineering stack."""
        classifier = IntentClassifier()
        generator = SpecGenerator()
        router = ModelRouter()

        # Layer 1: Intent Engineering — what are we trying to achieve?
        intent = classifier.classify("Create a landing page for a SaaS product with pricing tiers")
        assert intent.category == "landing_page"
        assert intent.quality_bar  # Has success criteria

        # Layer 2: Context Engineering — what info does the model need?
        spec = generator.generate(intent, user_context={
            "colors": "#0066ff, #ffffff, #f8f9fa",
            "target_audience": "B2B SaaS founders",
            "brand": "AcmeCorp",
        })
        assert "#0066ff" in spec.markdown
        assert "B2B SaaS" in spec.markdown
        assert "AcmeCorp" in spec.markdown

        # Layer 3: Prompt Engineering — how to phrase the instruction?
        choice = router.route(intent, phase="generation")
        assert choice.model == "minimax-m3"  # Creative for landing
        assert choice.temperature >= 0.7  # High temp for creativity
