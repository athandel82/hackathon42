# frontend module (ARCHITECTURE.md §4, §6)
# EC2 instance serving the React SPA. Reuses an existing VPC subnet and
# security group (per deployment guidance) — no networking is created here.

# Latest Amazon Linux 2023 x86_64 AMI (matches the t3 default instance type).
data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

resource "aws_instance" "frontend" {
  ami                         = data.aws_ssm_parameter.al2023.value
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [var.security_group_id]
  associate_public_ip_address = true
  key_name                    = var.key_name != "" ? var.key_name : null

  user_data = templatefile("${path.module}/user-data.sh.tftpl", {
    api_url           = var.api_url
    frontend_repo_url = var.frontend_repo_url
    frontend_subdir   = var.frontend_subdir
    port              = var.port
  })
  # Re-run user-data when its inputs change (replaces the instance).
  user_data_replace_on_change = true

  tags = {
    Name = "${var.name_prefix}-frontend"
  }
}
