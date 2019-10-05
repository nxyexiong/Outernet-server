# Outernet-server

An Outernet Linux server

## Usage

1. Run the server:

```
python3 main.py <MAIN_PORT> <SECRET>
```

2. Configure users:

```
sqlite3 profile.db
```

There are 3 columns in the table `users`. `name` is the attribute you use to verify client, `desc` is what you use to identify who the hell is this guy, which of course can be ignored. And the `traffic_remain` column is represent how many bytes this client can use. If a client ran out of traffic, it will be not able to transmit data any more, until you add it.
