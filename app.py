"""
StaleMind — Phase 4: Gradio Interactive Demo
Lets judges see drift happening, wrong decisions, and reward drops in real-time.
"""

import gradio as gr
import requests

BASE_URL = "https://mrhapile-stalemind.hf.space"

SCENARIOS = {
    "Easy (drift at step 7)": 0,
    "Medium (drift at step 5)": 1,
    "Hard (drift at step 3)": 2
}

AGENT_NAIVE = "Naive (always ACCEPT)"
AGENT_ADAPTIVE = "Adaptive (drift-aware)"

custom_css = """
/* Global Theme Adjustments */
body, .gradio-container {
    background-color: #0b0f19 !important;
    font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, sans-serif !important;
}

/* Header Enhancements */
h1 {
    color: #ffffff;
    font-weight: 800;
    letter-spacing: -0.02em;
}
.drift-text {
    color: #34d399;
    font-weight: 600;
}

/* Custom Cards */
.result-card {
    display: flex;
    align-items: center;
    background-color: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 16px;
    gap: 16px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    flex: 1;
}
.icon-box {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 24px;
}
.icon-box.reward {
    background-color: rgba(79, 70, 229, 0.15);
    color: #818cf8;
    border: 1px solid rgba(79, 70, 229, 0.3);
}
.icon-box.failure {
    background-color: rgba(225, 29, 72, 0.15);
    color: #fb7185;
    border: 1px solid rgba(225, 29, 72, 0.3);
}
.result-content {
    display: flex;
    flex-direction: column;
}
.result-label {
    color: #9ca3af;
    font-size: 13px;
    font-weight: 500;
    margin-bottom: 2px;
}
.result-value {
    font-size: 28px;
    font-weight: 700;
    line-height: 1;
}
.result-value.reward {
    color: #a78bfa;
}
.result-value.failure {
    color: #fb7185;
}

/* Button Styling */
#run-btn, #comp-btn {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    border: none !important;
    box-shadow: 0 4px 14px 0 rgba(79, 70, 229, 0.39) !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    border-radius: 8px !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    min-height: 52px !important;
}
#run-btn:hover, #comp-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.23) !important;
    background: linear-gradient(135deg, #4338ca, #6d28d9) !important;
}

/* Log Terminal */
.terminal-container {
    background-color: #111827;
    padding: 16px;
    overflow-x: auto;
}
.terminal-log {
    font-family: 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', monospace;
    font-size: 13px;
    line-height: 1.5;
    color: #d1d5db;
    margin: 0;
    white-space: pre;
}
.log-divider { color: #4b5563; }
.log-label { color: #a78bfa; font-weight: 600; }
.log-value { color: #f3f4f6; }
.log-accept { color: #34d399; }
.log-reject { color: #fbbf24; }
.log-drift { color: #60a5fa; font-weight: bold; background: rgba(96, 165, 250, 0.1); padding: 0 4px; border-radius: 4px; }
.log-fail { color: #f87171; font-weight: bold; background: rgba(248, 113, 113, 0.1); padding: 0 4px; border-radius: 4px; }

/* Wrapper for HTML widgets to fix height if needed */
.results-wrapper {
    display: flex;
    gap: 16px;
    margin-top: 8px;
    margin-bottom: 16px;
}
"""

theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="blue",
    neutral_hue="slate",
).set(
    body_background_fill="#0b0f19",
    body_text_color="#f3f4f6",
    block_background_fill="#111827",
    block_border_color="#1f2937",
    input_background_fill="#1f2937",
    color_accent="linear-gradient(135deg, #4f46e5, #7c3aed)",
)

def get_reward(result):
    r = result["reward"]
    return r["score"] if isinstance(r, dict) else r

def make_reward_card(reward):
    return f'''
    <div class="result-card">
        <div class="icon-box reward"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path><path d="M4 22h16"></path><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"></path></svg></div>
        <div class="result-content">
            <div class="result-label">Total Reward</div>
            <div class="result-value reward">{reward:.2f}</div>
        </div>
    </div>
    '''

def make_failure_card(fails):
    return f'''
    <div class="result-card">
        <div class="icon-box failure"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg></div>
        <div class="result-content">
            <div class="result-label">Failures</div>
            <div class="result-value failure">{fails}</div>
        </div>
    </div>
    '''

def format_terminal_log_to_html(scenario_name, agent_type, raw_log_data):
    lines = []
    lines.append('<span class="log-divider">' + '='*65 + '</span>')
    lines.append(f'<span class="log-label">Scenario:</span> <span class="log-value">{scenario_name}</span>')
    lines.append(f'<span class="log-label">Agent:</span> <span class="log-value">{agent_type}</span>')
    lines.append('<span class="log-divider">' + '='*65 + '</span>\\n')
    
    for step_data in raw_log_data:
        step = step_data['step']
        action_str = step_data['action']
        reward = step_data['reward']
        has_drift = step_data['has_drift']
        is_failure = step_data['is_failure']
        reasoning = step_data['reasoning']
        boss_v = step_data['boss_v']
        family_v = step_data['family_v']

        drift_tag = '  <span class="log-drift">[DRIFT]</span>' if has_drift else ""
        fail_tag = '  <span class="log-fail">[*** FAILURE ***]</span>' if is_failure else ""
        
        action_html = f'<span class="log-accept">{action_str:12s}</span>' if action_str == "ACCEPT" else f'<span class="log-reject">{action_str:12s}</span>'
        
        bars = min(max(int(abs(reward) * 10), 0), 10)
        bar_char = '+' if reward >= 0 else '-'
        reward_bar_str = bar_char * bars + '-' * (10 - bars)
        reward_span = f'<span class="log-accept">[{reward_bar_str}] {reward:.2f}</span>' if reward >= 0 else f'<span class="log-reject">[{reward_bar_str}] {reward:.2f}</span>'
        
        lines.append(f"Step {step:2d} | {action_html} | {reward_span}{drift_tag}{fail_tag}")
        lines.append(f"         <span style='color: #d1d5db;'>{reasoning}</span>")
        lines.append(f"         <span style='color: #60a5fa;'>Boss: {boss_v:.2f}</span>  <span style='color: #fb923c;'>Family: {family_v:.2f}</span>\\n")
        
    lines.append('<span class="log-divider">' + '='*65 + '</span>')
    
    html = f"""
    <div style="background-color: #111827; border: 1px solid #1f2937; border-radius: 12px; overflow: hidden;">
        <div style="background-color: #1f2937; padding: 12px 16px; border-bottom: 1px solid #374151; font-weight: 600; color: #f3f4f6; display: flex; align-items: center; gap: 8px;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
            Episode Log
        </div>
        <div class="terminal-container" style="border: none; border-radius: 0;">
            <pre class="terminal-log">{chr(10).join(lines)}</pre>
        </div>
    </div>
    """
    return html

def run_episode_core(scenario_name, agent_type):
    scenario_index = SCENARIOS[scenario_name]
    r = requests.post(f"{BASE_URL}/reset", json={"scenario_index": scenario_index})
    obs = r.json()["observation"]
    
    total_reward = 0.0
    failure_count = 0
    raw_log_data = []

    for step in range(10):
        msg = obs.get("message", "").lower()
        if agent_type == AGENT_NAIVE:
            action = {"type": "ACCEPT", "content": ""}
            reasoning = "Always accept work requests regardless of context"
        else:
            if any(w in msg for w in ["son", "event", "home", "needs you", "busy", "family", "needs"]):
                action = {"type": "REJECT", "content": "family priority"}
                reasoning = "Detected family signal in message -> rejecting work request"
            else:
                action = {"type": "ACCEPT", "content": "work priority"}
                reasoning = "No drift signal detected -> following work preference"

        r = requests.post(f"{BASE_URL}/step", json=action)
        result = r.json()
        reward = get_reward(result)
        done = result["done"]
        new_obs = result["observation"]

        has_drift = any(w in msg for w in ["son", "event", "home", "needs", "busy", "family"])
        is_failure = has_drift and action["type"] == "ACCEPT" and reward < 0.5
        if is_failure:
            failure_count += 1
            
        total_reward += reward
        
        raw_log_data.append({
            'step': step + 1,
            'action': action['type'],
            'reward': reward,
            'has_drift': has_drift,
            'is_failure': is_failure,
            'reasoning': reasoning,
            'boss_v': new_obs['relationships']['boss'],
            'family_v': new_obs['relationships']['family']
        })
        
        obs = new_obs
        if done: break
        
    return total_reward, failure_count, raw_log_data

def run_full_episode_ui(scenario_name, agent_type):
    tot, fail, raw = run_episode_core(scenario_name, agent_type)
    html_log = format_terminal_log_to_html(scenario_name, agent_type, raw)
    res_wrapper = f'<div class="results-wrapper">{make_reward_card(tot)}{make_failure_card(fail)}</div>'
    return html_log, res_wrapper

def run_comparison_ui(scenario_name):
    tot1, fail1, raw1 = run_episode_core(scenario_name, AGENT_NAIVE)
    tot2, fail2, raw2 = run_episode_core(scenario_name, AGENT_ADAPTIVE)
    
    html_log1 = format_terminal_log_to_html(scenario_name, AGENT_NAIVE, raw1)
    html_log2 = format_terminal_log_to_html(scenario_name, AGENT_ADAPTIVE, raw2)
    
    delta = tot2 - tot1
    comp_html = f"""
    <div style="background-color: #111827; border: 1px solid #1f2937; border-radius: 12px; overflow: hidden; margin-bottom: 24px;">
        <div style="background-color: #1f2937; padding: 12px 16px; border-bottom: 1px solid #374151; font-weight: 600; color: #f3f4f6; display: flex; align-items: center; gap: 8px;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
            Comparison Summary
        </div>
        <div style="padding: 16px;">
            <table style="width:100%; text-align:left; color:#d1d5db; border-collapse: collapse; margin-bottom: 16px;">
                <tr style="border-bottom: 1px solid #374151;">
                    <th style="padding: 8px 12px;">Agent</th>
                    <th style="padding: 8px 12px;">Total Reward</th>
                    <th style="padding: 8px 12px;">Failures</th>
                </tr>
                <tr style="border-bottom: 1px solid #374151;">
                    <td style="padding: 12px;">{AGENT_NAIVE}</td>
                    <td style="padding: 12px; color: #a78bfa; font-weight: bold; font-size: 18px;">{tot1:.2f}</td>
                    <td style="padding: 12px; color: #fb7185; font-size: 18px;">{fail1}</td>
                </tr>
                <tr>
                    <td style="padding: 12px;">{AGENT_ADAPTIVE}</td>
                    <td style="padding: 12px; color: #a78bfa; font-weight: bold; font-size: 18px;">{tot2:.2f}</td>
                    <td style="padding: 12px; color: #fb7185; font-size: 18px;">{fail2}</td>
                </tr>
            </table>
            <div style="padding: 12px 16px; background: rgba(52, 211, 153, 0.1); border-left: 4px solid #34d399; border-radius: 4px; color: #34d399; font-weight: 600; display: flex; align-items: center; gap: 8px;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>
                {delta:+.2f} reward improvement with aware agent
            </div>
        </div>
    </div>
    """
    
    return html_log1, html_log2, comp_html

# Build Gradio UI
with gr.Blocks(
    title="StaleMind — Drift Detection Demo",
    theme=theme,
    css=custom_css
) as demo:

    gr.Markdown("""
    # StaleMind — Preference Drift Simulation

    An RL-style environment demonstrating how AI agents fail when their understanding becomes **stale**.

    The environment presents work vs family scheduling conflicts. Mid-episode, the user's <span class="drift-text">true preferences shift</span>
    from "work > family" to "family > work" — but the agent only sees the original, stale preferences.

    ---
    """)

    with gr.Tab("Single Agent Run"):
        with gr.Row():
            scenario_input = gr.Dropdown(
                choices=list(SCENARIOS.keys()),
                value="Medium (drift at step 5)",
                label="Scenario"
            )
            agent_input = gr.Dropdown(
                choices=[AGENT_NAIVE, AGENT_ADAPTIVE],
                value=AGENT_ADAPTIVE,
                label="Agent Type"
            )
            run_btn = gr.Button("Run Episode", variant="primary", elem_id="run-btn")

        cards_output = gr.HTML()
        log_output = gr.HTML()

        run_btn.click(
            fn=run_full_episode_ui,
            inputs=[scenario_input, agent_input],
            outputs=[log_output, cards_output]
        )

    with gr.Tab("Naive vs Adaptive Comparison"):
        with gr.Row():
            comp_scenario = gr.Dropdown(
                choices=list(SCENARIOS.keys()),
                value="Medium (drift at step 5)",
                label="Scenario"
            )
            comp_btn = gr.Button("Run Comparison", variant="primary", elem_id="comp-btn")

        comp_summary = gr.HTML()

        with gr.Row():
            naive_output = gr.HTML()
            adaptive_output = gr.HTML()

        comp_btn.click(
            fn=run_comparison_ui,
            inputs=[comp_scenario],
            outputs=[naive_output, adaptive_output, comp_summary]
        )

    gr.Markdown("""
    ---
    **How it works:**
    - The environment runs 10 steps per episode
    - At a specific step (varies by difficulty), the hidden `true_preferences` flip
    - The agent only sees `visible_preferences: ["work > family"]` (never updated)
    - Soft signals appear in the observation message (e.g., "Your son needs you")
    - The **Naive agent** ignores these signals and keeps ACCEPTing → reward drops to ~0
    - The **Adaptive agent** detects drift signals and switches to REJECT → maintains high reward
    """)


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7861)
