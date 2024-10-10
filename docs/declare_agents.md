# Declare agents in YAML
agents:
  - name: "Agent1"
    description: "This agent performs data collection tasks."
    type: "data-collector"
    parameters:
      api_endpoint: "https://api.example.com/data"
      timeout: 30

  - name: "Agent2"
    description: "This agent analyzes collected data."
    type: "data-analyzer"
    parameters:
      analysis_method: "statistical"
      confidence_level: 95

  - name: "Agent3"
    description: "This agent generates reports based on analyzed data."
    type: "report-generator"
    parameters:
      output_format: "PDF"
      include_charts: true

  - name: "Agent4"
    description: "This agent sends notifications to users."
    type: "notification-sender"
    parameters:
      notification_method: "email"
      email_template: "default"
