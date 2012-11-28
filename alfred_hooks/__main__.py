import argparse
import multiprocessing
import msgpack
import yaml
import zmq

from .handlers import HooksHandler


def get_config(path):
    with open(path) as file:
        return yaml.load(file)


def run(config):
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.bind(config.get('hooks'))
    pool = multiprocessing.Pool(processes=config.get('num_workers'))
    try:
        while True:
            msg = socket.recv()
            task = msgpack.unpackb(msg, encoding='utf-8')
            pool.apply_async(HooksHandler.dispatch, args=(config, task))
    except KeyboardInterrupt:
        pass
    finally:
        pool.terminate()

    socket.close()
    context.term()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    args = parser.parse_args()
    config = get_config(args.config)
    run(config)


if __name__ == '__main__':
    main()
