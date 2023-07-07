import time

def test(net):

    # on first server start the listener
    net.get("h1").sendCmd("python3 -m http.server 9000 &")
    time.sleep(2)
    net.get("h2").sendCmd("python3 -m http.server 9000 &")
    time.sleep(2)
    net.get("h3").sendCmd("python3 -m http.server 9000 &")
    time.sleep(2)
    net.get("h4").sendCmd("python3 -m http.server 9000 &")
    time.sleep(2)
    net.get("h5").sendCmd("python3 -m http.server 9000 &")
    time.sleep(2)
    net.get("h6").sendCmd("python3 -m http.server 9000 &")
    time.sleep(2)
    print("Running base test with only one server")

    time.sleep(4)

    print(net['r3'])
    print("Done")
    return