# Remote environment for working on this tutorial

this pulumi script sets up a number of hcloud hosts using hetzner
how to use:


1. Edit index.ts to add the machines you need for this tutorial, every machine with a username and a password. off course, don't commit your edits
2. Set up pulumi:

```shell
# install pulumi
curl -sSL https://get.pulumi.com | sh
# create a local stack (alternative: create pulumi account)
pulumi login --local
# install SDK
npm install
```

> If you get weird errors in the above, check that your nodejs installation is recent (hint: the one that comes with ubuntu IS NOT RECENT. install the official one).

3. Go to cloud.hetzner.com, create a project and for this project get an API token.
4. Set the token

```shell
# change the passphrase if you didn't have it empty
PULUMI_CONFIG_PASSPHRASE="" pulumi config set --secret hcloud:token <YOURTOKEN>
```

5. Create the machines

```shell
PULUMI_CONFIG_PASSPHRASE="" pulumi up
```

6. Do the tutorial.

7. At the end, destroy everything

```shell
PULUMI_CONFIG_PASSPHRASE="" pulumi destroy
```
