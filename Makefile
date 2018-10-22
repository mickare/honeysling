NAME := mickare/honeysling
VERSION := 0.1
REPOSITORY := hub.docker.com

NO_CACHE := false

.PHONY: all build test tag_latest login logout release

all: build

build:
	docker build --no-cache=$(NO_CACHE) -t $(NAME):$(VERSION) --network=host --rm .

test:
	@echo "*** No test defined."

tag_latest:
	docker tag $(NAME):$(VERSION) $(REPOSITORY)/$(NAME):latest
	docker tag $(NAME):$(VERSION) $(REPOSITORY)/$(NAME):$(VERSION)

login:
	@grep -q $(REPOSITORY) ~/.docker/config.json \
		|| ( \
			echo "Login to the Docker registry \"$(REPOSITORY)\":" \
			&& docker login "$(REPOSITORY)" \
		)

logout:
	docker logout "$(REPOSITORY)"

release: login test tag_latest
	@if ! docker images $(NAME) | awk '{ print $$2 }' | grep -q -F $(VERSION); then echo "$(NAME) version $(VERSION) is not yet built. Please run 'make build'"; false; fi
	docker push $(REPOSITORY)/$(NAME)
