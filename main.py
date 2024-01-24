import re

from nornir import InitNornir
from nornir.core.filter import F
from nornir_scrapli.tasks import (
    send_command,
)
from nornir.core.exceptions import NornirExecutionError


def get_uptime(task):
    '''
    Получает информацию о времени работы устройства.

    :param task: Объект задачи Nornir
    :return: Общее время работы устройства в минутах или None в случае ошибки

    '''
    regex = r'\w+ +(?P<weeks>\d+).+?(?P<days>\d+).+?(?P<hours>\d+).+?(?P<minutes>\d+)' 
    try:
        get_version = task.run(
            task=send_command,
            command="sh ver",
        )

        current_uptime = get_version.result.strip().split('\n')[-1]
        match_uptime = re.search(regex, current_uptime)
        if match_uptime:
            weeks, days, hours, minutes = map(int, match_uptime.groups())
            total_minutes = weeks * 7 * 24 * 60 + days * 24 * 60 + hours * 60 + minutes
            return total_minutes
    except NornirExecutionError as error:
        print(f"Error accessing device {task.host.name}: {str(error)}")
    return None



def sort_devices(device_info):
    '''
    Функция для сортировки устройств по времени работы.

    :param device_info: Кортеж (хост, время работы в минутах)
    :return: Время работы устройства
    '''
    return device_info[1]


def format_uptime(device_info):
    '''
    Форматирует информацию о времени работы устройства для вывода.

    :param device_info: Кортеж (хост, время работы в минутах)
    :return: Строка с информацией о времени работы

    '''
    host, uptime_minutes = device_info
    
    if not isinstance(uptime_minutes, int):
        print(f"Error: Unexpected data type for uptime_minutes on {host}. Skipping.")
        return None

    weeks, days = divmod(uptime_minutes, 7 * 24 * 60)
    days, hours = divmod(days, 24 * 60)
    hours, minutes = divmod(hours, 60)
    return f"Device {host} uptime is {weeks} weeks, {days} days, {hours} hours, {minutes} minutes."


def collect_devices_info(result):
    '''
    Собирает информацию о времени работы устройств из результатов выполнения задач.

    :param result: Результат выполнения задач Nornir
    :return: Список кортежей (хост, время работы в минутах)
    '''
    devices_info = []
    for host, task_result in result.items():
        uptime_minutes = task_result.result
        if uptime_minutes is not None:
            devices_info.append((host, uptime_minutes))
    return devices_info


def main():
    '''
    Основная функция скрипта.

    Инициализирует Nornir, выполняет задачу получения времени работы, собирает информацию
    и выводит отсортированный результат. Сортировка убывающая.
    '''
    nr = InitNornir(config_file="./config.yaml")
    snr = nr.filter(F(groups__contains="snr"))
    result = snr.run(get_uptime)

    devices_info = collect_devices_info(result)
    sorted_devices = sorted(devices_info, key=sort_devices, reverse=True)
    for device_info in sorted_devices:
        print(format_uptime(device_info))


if __name__ == "__main__":
    main()
