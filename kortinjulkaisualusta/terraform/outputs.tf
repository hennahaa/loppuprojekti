output "url" {
  description = "The URL where the Cloud Run Service can be accessed."
  value       = google_cloud_run_service.kekkoslovakia.status[0].url
}

output "load_balancer_ip" {
  value = google_compute_global_address.default.address
}