# Hawk Logger

Hawk Logger is an Alexa skill and backend service for managing daily falconry logs using natural language input. It supports adding new birds, logging food and weight updates, recording behavioral notes, and querying missing data—all through spoken commands.

## Features

- Register birds with name and species
- Record daily weight, food amount, and performance
- Log enrichment and behavior notes
- Get reminders about missing data
- Uses MongoDB Atlas and OpenAI GPT for natural language parsing
- Deployable via AWS Lambda and SAM

## Usage Examples

- "Alexa, ask Hawk Logger to add a Harris Hawk named Ahab"
- "Alexa, ask Hawk Logger to log 24 grams of food for Ahab"
- "Alexa, ask Hawk Logger what info is still needed for Ahab"

## Development

This repo includes:

- `lambda_function.py` — The AWS Lambda handler with natural language processing
- `src/tests/` — Test suite and JSON test cases
- `.aws-sam/` — SAM build output
- `Makefile` — Common commands: `make test`, `make clean`

## Deployment

1. Deploy Lambda with AWS SAM
2. Connect to Alexa skill via the Developer Console
3. Add Alexa permission to Lambda:
   ```bash
   aws lambda add-permission      --function-name YOUR_FUNCTION_ARN      --statement-id AlexaInvokePermission      --action lambda:InvokeFunction      --principal alexa-appkit.amazon.com      --source-arn "amzn:ask:amzn1.ask.skill.YOUR_SKILL_ID"
   ```

## Privacy Policy and Terms

This skill does not collect personal data. See `privacy.md` and `terms.md` for details.