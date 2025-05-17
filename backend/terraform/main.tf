provider "aws" {
  region = var.aws_region
}

module "networking" {
  source = "./modules/networking"

  vpc_cidr            = "10.0.0.0/16"
  public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.3.0/24", "10.0.4.0/24"]
  availability_zones  = ["us-east-1a", "us-east-1b"]
}

module "database" {
  source = "./modules/database"

  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  db_instance_class  = "db.t3.micro"
  db_name            = "appdb"
  db_username        = var.db_username
  db_password        = var.db_password
}

module "lambda" {
  source = "./modules/lambda"

  vpc_id             = module.networking.vpc_id
  subnet_ids         = module.networking.private_subnet_ids
  security_group_ids = [module.networking.lambda_sg_id]
  
  failover_handler_role_arn = aws_iam_role.failover_handler.arn
  health_monitor_role_arn   = aws_iam_role.health_monitor.arn
  
  db_endpoint = module.database.primary_endpoint
  db_reader_endpoint = module.database.reader_endpoint
}

resource "aws_cloudwatch_event_rule" "health_check" {
  name                = "health-check-rule"
  description         = "Scheduled health check for database"
  schedule_expression = "rate(1 minute)"
}

resource "aws_cloudwatch_event_target" "health_check_lambda" {
  rule      = aws_cloudwatch_event_rule.health_check.name
  target_id = "HealthMonitorLambda"
  arn       = module.lambda.health_monitor_arn
}

resource "aws_sns_topic" "failover_notifications" {
  name = "failover-notifications"
}

resource "aws_cloudwatch_metric_alarm" "db_failover" {
  alarm_name          = "database-failover-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "DatabaseFailoverTriggered"
  namespace          = "Custom"
  period             = "60"
  statistic          = "Sum"
  threshold          = "0"
  alarm_description  = "This metric triggers database failover"
  alarm_actions      = [module.lambda.failover_handler_arn]
}