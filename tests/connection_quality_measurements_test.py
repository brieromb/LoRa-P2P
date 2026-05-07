from lora_p2p.receiving.received_message import ConnectionQualityMeasurements

def test_conn_qual_meas():
    conn_qual = ConnectionQualityMeasurements(1, 2)
    conn_qual1 = ConnectionQualityMeasurements(3, 5, 100000.0)
    conn_qual2 = ConnectionQualityMeasurements()
    print(conn_qual)
    print(conn_qual1)
    print(conn_qual2)

    conn_qual += conn_qual1
    print(conn_qual)
    print(conn_qual1)