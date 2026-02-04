terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  profile = var.aws_profile
}

locals {
  lambda_zip = var.lambda_zip_path
}

resource "aws_dynamodb_table" "bots" {
  name         = var.bots_table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "bot_id"

  attribute {
    name = "bot_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "runs" {
  name         = var.runs_table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "run_id"

  attribute {
    name = "run_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "tokens" {
  name         = var.tokens_table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "token_id"

  attribute {
    name = "token_id"
    type = "S"
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "flip7-hosted-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "flip7-hosted-lambda-policy"
  role = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.lambda_policy.json
}

data "aws_iam_policy_document" "lambda_policy" {
  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Scan"
    ]
    resources = [
      aws_dynamodb_table.bots.arn,
      aws_dynamodb_table.runs.arn,
      aws_dynamodb_table.tokens.arn
    ]
  }

  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }

  statement {
    actions = ["xray:PutTraceSegments", "xray:PutTelemetryRecords"]
    resources = ["*"]
  }
}

resource "aws_lambda_function" "submit_bot" {
  function_name = "flip7-submit-bot"
  role          = aws_iam_role.lambda_role.arn
  handler       = "hosted_api.handlers.submit_bot.handler"
  runtime       = "python3.11"
  timeout       = 900

  filename         = local.lambda_zip
  source_code_hash = filebase64sha256(local.lambda_zip)

  environment {
    variables = {
      BOTS_TABLE   = var.bots_table
      RUNS_TABLE   = var.runs_table
      TOKENS_TABLE = var.tokens_table
      SHOW_CODE_TOP_N = var.show_code_top_n
      BOT_TIMEOUT_SECONDS = var.bot_timeout_seconds
    }
  }

  tracing_config {
    mode = "Active"
  }
}

resource "aws_lambda_function" "get_my_bot" {
  function_name = "flip7-get-my-bot"
  role          = aws_iam_role.lambda_role.arn
  handler       = "hosted_api.handlers.get_my_bot.handler"
  runtime       = "python3.11"
  timeout       = 60

  filename         = local.lambda_zip
  source_code_hash = filebase64sha256(local.lambda_zip)

  environment {
    variables = {
      BOTS_TABLE   = var.bots_table
      RUNS_TABLE   = var.runs_table
      TOKENS_TABLE = var.tokens_table
      SHOW_CODE_TOP_N = var.show_code_top_n
      BOT_TIMEOUT_SECONDS = var.bot_timeout_seconds
    }
  }

  tracing_config { mode = "Active" }
}

resource "aws_lambda_function" "run_tournament" {
  function_name = "flip7-run-tournament"
  role          = aws_iam_role.lambda_role.arn
  handler       = "hosted_api.handlers.run_tournament.handler"
  runtime       = "python3.11"
  timeout       = 900

  filename         = local.lambda_zip
  source_code_hash = filebase64sha256(local.lambda_zip)

  environment {
    variables = {
      BOTS_TABLE   = var.bots_table
      RUNS_TABLE   = var.runs_table
      TOKENS_TABLE = var.tokens_table
      SHOW_CODE_TOP_N = var.show_code_top_n
      BOT_TIMEOUT_SECONDS = var.bot_timeout_seconds
    }
  }

  tracing_config { mode = "Active" }
}

resource "aws_lambda_function" "publish_leaderboard" {
  function_name = "flip7-publish-leaderboard"
  role          = aws_iam_role.lambda_role.arn
  handler       = "hosted_api.handlers.publish_leaderboard.handler"
  runtime       = "python3.11"
  timeout       = 60

  filename         = local.lambda_zip
  source_code_hash = filebase64sha256(local.lambda_zip)

  environment {
    variables = {
      BOTS_TABLE   = var.bots_table
      RUNS_TABLE   = var.runs_table
      TOKENS_TABLE = var.tokens_table
      SHOW_CODE_TOP_N = var.show_code_top_n
      BOT_TIMEOUT_SECONDS = var.bot_timeout_seconds
    }
  }

  tracing_config { mode = "Active" }
}

resource "aws_lambda_function" "get_leaderboard" {
  function_name = "flip7-get-leaderboard"
  role          = aws_iam_role.lambda_role.arn
  handler       = "hosted_api.handlers.get_leaderboard.handler"
  runtime       = "python3.11"
  timeout       = 60

  filename         = local.lambda_zip
  source_code_hash = filebase64sha256(local.lambda_zip)

  environment {
    variables = {
      BOTS_TABLE   = var.bots_table
      RUNS_TABLE   = var.runs_table
      TOKENS_TABLE = var.tokens_table
      SHOW_CODE_TOP_N = var.show_code_top_n
      BOT_TIMEOUT_SECONDS = var.bot_timeout_seconds
    }
  }

  tracing_config { mode = "Active" }
}

resource "aws_apigatewayv2_api" "http_api" {
  name          = "flip7-hosted-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "submit_bot" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.submit_bot.invoke_arn
}

resource "aws_apigatewayv2_integration" "get_my_bot" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.get_my_bot.invoke_arn
}

resource "aws_apigatewayv2_integration" "run_tournament" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.run_tournament.invoke_arn
}

resource "aws_apigatewayv2_integration" "publish_leaderboard" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.publish_leaderboard.invoke_arn
}

resource "aws_apigatewayv2_integration" "get_leaderboard" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.get_leaderboard.invoke_arn
}

resource "aws_apigatewayv2_route" "submit_bot" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /bots/submit"
  target    = "integrations/${aws_apigatewayv2_integration.submit_bot.id}"
}

resource "aws_apigatewayv2_route" "get_my_bot" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /bots/me"
  target    = "integrations/${aws_apigatewayv2_integration.get_my_bot.id}"
}

resource "aws_apigatewayv2_route" "run_tournament" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /admin/tournament/run"
  target    = "integrations/${aws_apigatewayv2_integration.run_tournament.id}"
}

resource "aws_apigatewayv2_route" "publish_leaderboard" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /admin/leaderboard/publish"
  target    = "integrations/${aws_apigatewayv2_integration.publish_leaderboard.id}"
}

resource "aws_apigatewayv2_route" "get_leaderboard" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /leaderboard/current"
  target    = "integrations/${aws_apigatewayv2_integration.get_leaderboard.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_submit_bot" {
  statement_id  = "AllowAPIGatewaySubmitBot"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.submit_bot.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_get_my_bot" {
  statement_id  = "AllowAPIGatewayGetMyBot"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_my_bot.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_run_tournament" {
  statement_id  = "AllowAPIGatewayRunTournament"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.run_tournament.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_publish_leaderboard" {
  statement_id  = "AllowAPIGatewayPublishLeaderboard"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.publish_leaderboard.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_get_leaderboard" {
  statement_id  = "AllowAPIGatewayGetLeaderboard"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_leaderboard.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

resource "aws_cloudwatch_event_rule" "nightly_tournament" {
  name                = "flip7-nightly-tournament"
  schedule_expression = "cron(0 7 * * ? *)"
}

resource "aws_cloudwatch_event_target" "nightly_tournament" {
  rule      = aws_cloudwatch_event_rule.nightly_tournament.name
  target_id = "flip7-run-tournament"
  arn       = aws_lambda_function.run_tournament.arn
  input     = jsonencode({
    games_per_matchup_h2h = 1000,
    games_per_matchup_all = 10000,
    seed = 42,
    auto_publish = true
  })
}

resource "aws_lambda_permission" "events_run_tournament" {
  statement_id  = "AllowEventBridgeRunTournament"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.run_tournament.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.nightly_tournament.arn
}
