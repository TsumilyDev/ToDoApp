def memory_demonstration():
    import memory
    from time import sleep

    mem = memory.Memory("test")

    mem.add_container("test")
    mem.add_data("test_container", "identifier", 10, "data")
    print(mem.retrieve_data("test_container", "identifier"))  # "data"
    mem.delete_data("test_container", "identifier")

    mem.add_data("test_container", "identifier", 1, "data")
    sleep(1)
    mem.retrieve_data(
        "test_container", "identifier"
    )  # Throws a DataExpiredError


if __name__ == "__main__":
    memory_demonstration()
