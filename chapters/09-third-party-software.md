# Working with third party software

So far we used helm and skaffold, but we used it with our own helm chart. However, in many cases, you won't have to do that as a helm chart for the software you want to use is already out there.

## Choosing your helm chart

Often, for some software there are multiple helm charts available. You will need to choose which one. Choose wisely:

* Take one that is still maintained (recent versions, activity on github)
* If possible take one from the authors of the software. If not, take one from a reputable organisation.
* When taking a helm chart from github, don't just take master branch, but take a released version.
* Have a look at the open issues. The helm chart might have a security issue or might be incompatible with your version of kubernetes.

## Installing a helm chart from git

Helm charts can be published in git repo's. To install them, clone the git repo, go to the right folder, look at the values you want to override and install away. This is actually the same process we used for our own helm chart.

## Helm repositories

There is actually another way to install helm charts: using helm repositories. A helm repository is just a collection of zipped up helm charts somewhere on the web. A helm repository has one file that should always be present: `index.yaml`. This file contains the list of all helm charts on that repository.

Excercise: installing CVAT from https://github.com/Kapernikov/cvat-helm

* First add the repository
* Then use 'helm show values'  to see which values are available and what are their default settings.
* Then use helm install. Use the `--set` flag to override some values.

## Operators

Extra time excercise:

* install the zalando postgres operator
* create a postgres cluster
