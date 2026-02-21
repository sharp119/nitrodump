// nitrodump Übersicht Widget
// https://github.com/felixhageloh/uebersicht

// Command to execute
export const command = "/Users/adityapaswan/.local/bin/nitrodump --json";

// Refresh interval (in milliseconds)
export const refreshFrequency = 60000;

// CSS styling for the widget
export const className = `
  /* Position on the desktop */
  top: 20px;
  right: 20px;
  
  /* Font and styling */
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
  color: #fff;
  
  /* Glassmorphism background */
  background: rgba(15, 15, 20, 0.45);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
  
  /* Layout */
  padding: 16px 20px;
  min-width: 260px;
  
  h1 {
    font-size: 11px;
    margin: 0 0 12px 0;
    color: rgba(255, 255, 255, 0.6);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 600;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 8px;
  }

  .status-indicator {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: #34c759;
    box-shadow: 0 0 8px #34c759;
  }
  
  .model-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .model {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 13px;
  }
  
  .model-name {
    font-weight: 500;
  }
  
  .model-pct {
    font-feature-settings: "tnum";
    font-variant-numeric: tabular-nums;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.1);
  }

  /* Custom colors based on percentage */
  .pct-high { color: #34c759; }
  .pct-med { color: #ffcc00; }
  .pct-low { color: #ff3b30; }

  .error {
    color: #ff3b30;
    font-size: 12px;
  }
`;

// Render function for the UI
export const render = ({ output, error }) => {
  if (error) {
    return (
      <div>
        <h1>Nitrodump Error</h1>
        <div className="error">{String(error)}</div>
      </div>
    );
  }
  
  let data;
  try {
    data = JSON.parse(output);
  } catch (e) {
    return (
      <div>
        <h1>Nitrodump Parser Error</h1>
        <div className="error">Failed to read JSON output. Is nitrodump installed correctly?</div>
      </div>
    );
  }
  
  const status = data.user_status;
  const planName = status.plan_status.plan_info.plan_name || "Unknown Plan";
  
  // Extract and format the models
  const configs = status.cascade_model_config_data?.client_model_configs || [];
  const models = configs.map(config => {
    let name = config.label;
    
    // Create short beautiful display names
    let shortName = name;
    if (name.includes("Opus")) shortName = "Claude 3 Opus";
    else if (name.includes("Sonnet")) shortName = "Claude 3.5 Sonnet";
    else if (name.includes("GPT-OSS")) shortName = "GPT-OSS 120B";
    else if (name.includes("Flash")) shortName = "Gemini 1.5 Flash";
    else if (name.includes("Gemini 3 Pro (High)")) shortName = "Gemini 3 Pro (H)";
    else if (name.includes("Gemini 3 Pro (Low)")) shortName = "Gemini 3 Pro (L)";
    else if (name.includes("Gemini 3.1 Pro (High)")) shortName = "Gemini 3.1 Pro (H)";
    else if (name.includes("Gemini 3.1 Pro (Low)")) shortName = "Gemini 3.1 Pro (L)";
    else shortName = name.substring(0, 16);
    
    // Get percentage (e.g. 0.8 -> 80)
    const pct = parseInt(config.quota_info.remaining_fraction * 100, 10);
    
    // Determine color class
    let colorClass = "pct-high";
    if (pct <= 20) colorClass = "pct-low";
    else if (pct <= 70) colorClass = "pct-med";
    
    return { name: shortName, pct, colorClass };
  });
  
  return (
    <div>
      <h1>
        NITRODUMP: {planName.toUpperCase()}
        <div className="status-indicator"></div>
      </h1>
      <div className="model-list">
        {models.map(m => (
          <div className="model" key={m.name}>
            <span className="model-name">{m.name}</span>
            <span className={"model-pct " + m.colorClass}>
              {m.pct}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
