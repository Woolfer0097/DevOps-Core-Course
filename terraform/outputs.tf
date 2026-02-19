output "vm_public_ip" {
  description = "Public IP address of the VM"
  value       = yandex_compute_instance.lab.network_interface[0].nat_ip_address
}

output "vm_private_ip" {
  description = "Private IP address of the VM"
  value       = yandex_compute_instance.lab.network_interface[0].ip_address
}

output "vm_id" {
  description = "ID of the created VM"
  value       = yandex_compute_instance.lab.id
}

output "ssh_command" {
  description = "SSH connection command"
  value       = "ssh ${var.vm_user}@${yandex_compute_instance.lab.network_interface[0].nat_ip_address}"
}
