output "public_dns" {
  value = aws_instance.frontend.public_dns
}

output "public_ip" {
  value = aws_instance.frontend.public_ip
}

output "instance_id" {
  value = aws_instance.frontend.id
}

output "url" {
  description = "Best-effort URL to reach the SPA."
  value       = "http://${aws_instance.frontend.public_dns}:${var.port}/"
}
