output "vpc_id" {
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  value       = { for k, v in aws_subnet.public : k => v.id }
}

output "private_subnet_ids_list" {
  value       = [for subnet in aws_subnet.private : subnet.id]
}

output "nat_gateway_ips" {
  value = var.enable_nat_gateway ? aws_eip.nat["default"].public_ip : null
}

output "public_route_table_id" {
  value       = aws_route_table.public.id
}
