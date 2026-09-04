# Decrypt secrets for ESPHome, then flash.
# Requires: sops + age, with the shared age key at ~/.config/sops/age/keys.txt

secrets: secrets.yaml

secrets.yaml: secrets.enc.yaml
	sops -d secrets.enc.yaml > secrets.yaml

run: secrets
	esphome run cleanaircabinet.yaml

.PHONY: secrets run
