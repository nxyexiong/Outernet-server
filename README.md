# Outernet-server

An Outernet Linux server

## Usage

1. create ```user.yaml``` like shown:

```
{
  users: [
    'user0',
    'user1',
  ]
}
```

2. run the server:

```
python3 main.py <MAIN_PORT> <SECRET>
```

## TODO

1. improve speed
2. improve traffic counter