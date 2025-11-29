# ThreatIntelCollector
A set of scripts and kubernetes jobs to grab TI reports from various Github repos

# docker build
Since I'm building this on a mac, but running it on x86, I need to cross compile
the docker image.
`docker buildx build --platform linux/amd64,linux/arm64 . -t ticollector:1.5`
