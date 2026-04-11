output "server_public_ip" {
  description = "The public IP of the newly created backend server"
  value       = aws_instance.production_server.public_ip
}

# Generate an inventory file on the fly for Ansible!
resource "local_file" "ansible_inventory" {
  content = <<EOF
[webservers]
${aws_instance.production_server.public_ip} ansible_user=ubuntu ansible_ssh_private_key_file=./server_key.pem
EOF
  filename = "${path.module}/../ansible/inventory.ini"
}
