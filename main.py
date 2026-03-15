import click
import os
import json
from datetime import datetime
from src.ai_generator import AITestGenerator
from src.parser import TestCaseParser
from src.test_runner import TestRunner

@click.group()
def cli():
    """🤖 AI Test-Case Generator — Powered by Hugging Face"""
    pass

@cli.command()
@click.option('--feature', '-f', required=True, 
              help='Feature to test (e.g., "user login page")')
@click.option('--count', '-n', default=5, 
              help='Number of test cases to generate (default: 5)')
@click.option('--run/--no-run', default=True,
              help='Automatically run generated tests')
def generate(feature, count, run):
    """Generate and optionally run AI-powered test cases."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    feature_slug = feature.replace(" ", "_")[:30]
    
    # File paths
    json_path = f"tests/generated/tc_{feature_slug}_{timestamp}.json"
    pytest_path = f"tests/generated/test_{feature_slug}_{timestamp}.py"
    report_path = f"reports/report_{feature_slug}_{timestamp}.html"
    
    os.makedirs("tests/generated", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    # Step 1: Generate with AI
    generator = AITestGenerator()
    raw_output = generator.generate_test_cases(feature, count)
    
    # Step 2: Parse the output
    parser = TestCaseParser()
    test_cases = parser.parse(raw_output)
    parser.save_to_json(test_cases, json_path)
    
    # Step 3: Create pytest file
    runner = TestRunner()
    runner.generate_pytest_file(test_cases, pytest_path)
    
    # Step 4: Run tests if requested
    if run:
        results = runner.run_tests(pytest_path, report_path)
        click.echo(f"\n{'='*50}")
        click.echo(f"✅ Passed: {results['passed']}")
        click.echo(f"❌ Failed: {results['failed']}")
        click.echo(f"📄 Full report: {report_path}")

@cli.command()
@click.option('--feature', '-f', required=True,
              help='Feature to discuss with AI')
def chat(feature):
    """Conversational mode — refine test cases interactively."""
    generator = AITestGenerator()
    parser = TestCaseParser()
    
    click.echo(f"💬 Chat mode for: {feature}")
    click.echo("Commands: 'add edge cases', 'make stricter', 'add negative tests', 'quit'\n")
    
    # Generate initial cases
    raw = generator.generate_test_cases(feature, 3)
    test_cases = parser.parse(raw)
    click.echo(f"Generated {len(test_cases)} initial test cases.\n")
    
    while True:
        user_input = click.prompt("You")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        
        # Refine with AI
        refine_prompt = f"Feature: {feature}. User request: {user_input}. Generate 3 more test cases focusing on this request."
        raw = generator.generate_test_cases(refine_prompt, 3)
        new_cases = parser.parse(raw)
        test_cases.extend(new_cases)
        click.echo(f"✅ Added {len(new_cases)} more test cases. Total: {len(test_cases)}\n")

if __name__ == '__main__':
    cli()