variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "aws_profile" {
  type    = string
  default = "flip-seven"
}

variable "lambda_zip_path" {
  type    = string
  default = "../../artifacts/flip7_hosted_lambda.zip"
}

variable "bots_table" {
  type    = string
  default = "Flip7Bots"
}

variable "runs_table" {
  type    = string
  default = "Flip7TournamentRuns"
}

variable "tokens_table" {
  type    = string
  default = "Flip7Tokens"
}

variable "show_code_top_n" {
  type    = number
  default = 0
}

variable "bot_timeout_seconds" {
  type    = number
  default = 1.0
}
