import sys

from machine import  RingMachine

def main():
    '''
        Utilization: python servidor.py [machine_id]
            machine_id -> varia de 0 a 3. Se for zero, vai esperar a
            mensagem das próximas
    '''

    if len(sys.argv) < 2 or int(sys.argv[1]) > 3:
        print("Utilization: python servidor.py [0 <= machine_id < 4]")

    machine_id = int(sys.argv[1])

    try:
        machine = RingMachine(machine_id)
        machine.run()
    except Exception as e:
        print(f"Falha ao inicializar máquinas: {e}")
        return

    except KeyboardInterrupt:
        print("\nCtrl+C detectado. Iniciando desligamento...")
        machine.close_socket()

    finally:
        print("Limpando recursos...")
        print("Programa finalizado.")

if __name__ == "__main__":
    main()