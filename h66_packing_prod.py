from quart import (
    Quart,
    request,
    render_template,
    url_for,
    redirect,
    jsonify,
    session,
    flash,
)
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from datetime import datetime
from functools import wraps
import webbrowser
import threading
import logging
import aioodbc
import asyncio
import serial
import os
from aiofiles import open as aio_open
import aiosmtplib
import configparser

logging.basicConfig(
    filename="h66_packing_app.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)

ser = None
messages = []

script_directory = os.path.dirname(os.path.abspath(__file__))
output_excel = os.path.join(script_directory, "Packed Box")
config_file = os.path.join(script_directory, "example.ini")
icon_path = os.path.join(script_directory, "icon", "image.ico")

folder_list = ["Packed Box", "icon"]

for folder in folder_list:
    if not os.path.exists(folder):
        os.makedirs(folder)
        logging.info(f"Making {folder}")
    else:
        logging.info(f"Folder {folder} already exist")

app = Quart(__name__)
app.secret_key = "you_will_never_guess"

config_data = configparser.ConfigParser()
config_data.read(config_file)

# database
db = config_data["database_details"]

# scanner configurations
scan = config_data["scanner"]
com_port = scan["com_port"]
print(com_port)

# box_settings
box_setting = config_data["box_setting"]
box_len = int(box_setting["box_len"])
box_start = box_setting["box_start"]

# part_settings
part_setting = config_data["part_setting"]
part_len = int(part_setting["part_len"])
part_starts = part_setting["part_start"]

# multiguage setting
multi_admin = config_data["multiguage"]
multi_set = multi_admin["m_setting"]

# group type setting
set_group_type = config_data["group_type"]
a_lower = set_group_type["A_lower"]
a_upper = set_group_type["A_upper"]
b_lower = set_group_type["B_lower"]
b_upper = set_group_type["B_upper"]
c_upper = set_group_type["C_upper"]

try:
    ser = serial.Serial(com_port, baudrate=9600, timeout=1)
    print("Serial Port Connected")
except serial.SerialException:
    print("Serial Port Disconnected")

# Database Connection String
dsn = (
    f"DRIVER={{SQL Server}};SERVER={db['server']};DATABASE={db['database']};UID={db['username']};PWD={db['password']}"
    f";TrustServerCertificate=yes "
)

users = {"admin": "ktfl@123"}

logging.getLogger("hypercorn.access").disabled = True


async def db_conn_all(query):
    try:
        conn = await aioodbc.connect(dsn=dsn)
        cur = await conn.cursor()
        await cur.execute(query)
        results = await cur.fetchall()
        await cur.close()
        await conn.close()
        return results
    except Exception as e:
        print(f"{e}")
        return []


async def db_conn_one(query):
    try:
        conn = await aioodbc.connect(dsn=dsn)
        cur = await conn.cursor()
        await cur.execute(query)
        r = await cur.fetchone()
        await cur.close()
        await conn.close()
        return r
    except Exception as e:
        print(f"{e}")
        return []


async def db_conn_commit(query):
    try:
        conn = await aioodbc.connect(dsn=dsn)
        cur = await conn.cursor()
        await cur.execute(query)
        await cur.commit()
        await cur.close()
        await conn.close()
    except Exception as e:
        print(f"{e}")


def login_required(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return await f(*args, **kwargs)

    return decorated_function


def authenticate(username, password):
    if users is None:
        return False
    return users.get(username) == password


async def status_H66_1_GRT(part_id):
    if multi_set == "True":
        status_check_query = f"SELECT TOP 1 RESULT_ID FROM [24M1570200_H66_1_GRT] WHERE PART_NBR = '{part_id}' ORDER BY Time_Stamp DESC"
        status = await db_conn_one(status_check_query)
        return status[0] if status else None


async def status_H66_1_MULTIGAUGING(part_id):
    if multi_set == "True":
        status_check_query = f"SELECT TOP 1 RESULT_ID FROM [24M1570200_H66_1_MULTIGAUGING] WHERE PART_NBR = '{part_id}' ORDER BY Time_Stamp DESC"
        status = await db_conn_one(status_check_query)
        return status[0] if status else None


async def status_H66_2_GRT(part_id):
    if multi_set == "True":
        status_check_query = f"SELECT TOP 1 RESULT_ID FROM [24M1570100_H66_2_GRT] WHERE PART_NBR = '{part_id}' ORDER BY Time_Stamp DESC"
        status = await db_conn_one(status_check_query)
        return status[0] if status else None


async def status_H66_2_MULTIGAUGING(part_id):
    if multi_set == "True":
        status_check_query = f"SELECT TOP 1 RESULT_ID FROM [24M1570100_H66_2_MULTIGAUGING] WHERE PART_NBR = '{part_id}' ORDER BY Time_Stamp DESC"
        status = await db_conn_one(status_check_query)
        return status[0] if status else None


async def count_part_dual_motor(box_id):
    count_sql = f"SELECT COUNT(*) AS box_count FROM H66_PACKING_PART_MASTER WHERE box_id = '{box_id}'"
    count_result = await db_conn_one(count_sql)
    if count_result:
        max_part_count = count_result[0]
        part_counter_dual_motor = max_part_count
        print("Max part count for box_id", box_id, ":", max_part_count)
        logging.info(f'"Max part count for box_id", {box_id}, ":", {max_part_count}')
    else:
        print("No records found for box_id", box_id)
        logging.info(f"No records found for box_id: {box_id}")
        part_counter_dual_motor = 0
    return part_counter_dual_motor


async def get_honing_type(part_id):
    honing_check = f"""SELECT TOP 1 honing_type, dresser_id 
        FROM HONING_PART_MASTER 
        WHERE part_id = '{part_id}'
        ORDER BY date_time DESC"""
    result = await db_conn_all(honing_check)
    return result[0][0], result[0][1] if result else None


async def junkar_part_check(part_id):
    junkar_check = (
        f"SELECT 1 FROM H66_OD_MACHINE_PART_MASTER WHERE junkar_part_id = '{part_id}'"
    )
    result = await db_conn_one(junkar_check)
    return "Yes" if result else "No"


async def group_type_check(part_id):
    check_grt_1_sql = f"""SELECT TOP 1 D8 FROM [24M1570200_H66_1_GRT] 
                        WHERE part_nbr = '{part_id}' ORDER BY Time_Stamp DESC"""
    check_grt_1 = await db_conn_one(check_grt_1_sql)

    if check_grt_1 is None:
        check_grt_2_sql = f"""SELECT TOP 1 D8 FROM [24M1570100_H66_2_GRT]
                          WHERE part_nbr = '{part_id}' ORDER BY Time_Stamp DESC"""
        check_grt_2 = await db_conn_one(check_grt_2_sql)

        if check_grt_2 is None:
            return None
        else:
            d8_grt_2 = float(check_grt_2[0])
            if float(a_lower) <= d8_grt_2 <= float(a_upper):
                return "A"
            elif float(b_lower) <= d8_grt_2 <= float(b_upper):
                return "B"
            elif d8_grt_2 >= float(c_upper):
                return "C"
    else:
        d8_grt_1 = float(check_grt_1[0])
        if float(a_lower) <= d8_grt_1 <= float(a_upper):
            return "A"
        elif float(b_lower) <= d8_grt_1 <= float(b_upper):
            return "B"
        elif d8_grt_1 >= float(c_upper):
            return "C"


@app.route("/message", methods=["POST", "GET"])
@login_required
async def message_notify():
    message_list = messages.copy()
    messages.clear()
    return jsonify(message_list)


@app.route("/", methods=["POST", "GET"])
@app.route("/login", methods=["POST", "GET"])
async def login():
    if request.method == "POST":
        form = await request.form
        username = form.get("username")
        password = form.get("password")

        box_redirect_query = """
            SELECT TOP 1 box_id, status, group_type
            FROM H66_PACKING_MASTER ORDER BY date_time DESC
        """
        box_redirect_list = await db_conn_one(box_redirect_query)
        print(box_redirect_list)

        def box_redirect():
            if box_redirect_list:
                box_id, group_type, status = (
                    box_redirect_list[0],
                    box_redirect_list[2],
                    box_redirect_list[1],
                )

                if status is None:
                    return box_id, group_type, True
                else:
                    return box_id, group_type, False
            else:
                return None, None, False

        box_id, group_type, should_redirect = box_redirect()
        if authenticate(username, password) and should_redirect is False:
            session["username"] = username
            return redirect(url_for("packing_selection"))
        elif authenticate(username, password) and should_redirect is True:
            session["username"] = username
            return redirect(
                url_for("packing_scan", box_id=box_id, group_type=group_type)
            )
        else:
            return redirect(url_for("login"))
    return await render_template("login.html")


@app.route("/logout")
async def logout():
    session.clear()
    return """
    <script>
    localStorage.setItem("logged_out", "true");  // Set logout flag in local storage
    localStorage.removeItem("logged_out");  // Immediate removal after setting
    window.location.href = '/login';  // Redirect to login page
    </script>
    """


@app.route("/packing_selection", methods=["POST", "GET"])
@login_required
async def packing_selection():
    box_id_error_msg = []

    get_last_box_id_query = (
        "SELECT TOP 1 box_id FROM H66_PACKING_MASTER ORDER BY date_time DESC"
    )
    get_last_box_id = await db_conn_one(get_last_box_id_query)

    if get_last_box_id:
        get_last_box_id = get_last_box_id[0]
    else:
        get_last_box_id = "This is your first box"

    if request.method == "POST":
        form = await request.form
        box_id_form = form.get("box_id")
        group_type = form.get("group_options")
        operator_name = form.get("operator_name")

        print(group_type, operator_name)

        if box_id_form.startswith(box_start) and len(box_id_form) == box_len:
            box_id = box_id_form
            top_box_sql = f"SELECT 1 FROM H66_PACKING_MASTER WHERE box_id = '{box_id}'"
            top_box_row = await db_conn_one(top_box_sql)
            if top_box_row:
                print(f"Box ID {box_id} is duplicate")
                await flash(f"Box ID {box_id} is duplicate", "error")
                logging.info(f"Box ID {box_id} is duplicate")
                return await render_template(
                    "packing_selection.html",
                    last_box_id=get_last_box_id,
                    error_msg=box_id_error_msg,
                )
            else:
                box_id_query = (
                    "SELECT box_id FROM H66_PACKING_MASTER WHERE status is null"
                )
                box_id_row = await db_conn_one(box_id_query)
                if box_id_row:
                    box_id = box_id_row[0]
                    print(f"Complete the existing box {box_id}")
                    await flash(f"Complete the existing box {box_id}", "error")
                    logging.info(f"Complete the existing box {box_id}")
                    return await render_template(
                        "packing_selection.html",
                        last_box_id=get_last_box_id,
                        error_msg=box_id_error_msg,
                    )
                else:
                    zero = 0
                    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    insert_query = f"""INSERT INTO H66_PACKING_MASTER (box_id, date_time, group_type, part_qty, operator_name) 
                        VALUES ('{box_id}', '{current_datetime}', '{group_type}', '{zero}','{operator_name}')"""
                    await db_conn_commit(insert_query)
                    print(f"Box ID {box_id} accepted and saved")
                    messages.append(
                        {
                            "type": "success",
                            "message": f"Box ID {box_id} accepted and saved",
                        }
                    )
                    logging.info(f"Box ID {box_id} accepted and saved")
                    return redirect(
                        url_for(
                            "packing_scan",
                            group_type=group_type,
                            operator_name=operator_name,
                            box_id=box_id,
                        )
                    )
        elif box_id_form:
            print("Box ID is not in proper format")
            await flash("Box ID is not in proper format", "error")
            logging.info("Box ID is not in proper format")
        return await render_template(
            "packing_selection.html",
            last_box_id=get_last_box_id,
            error_msg=box_id_error_msg,
        )

    return await render_template(
        "packing_selection.html",
        last_box_id=get_last_box_id,
        error_msg=box_id_error_msg,
    )


@app.route("/packing_summary")
@login_required
async def dresser_summary():
    packing_master = "SELECT * FROM H66_PACKING_MASTER ORDER BY date_time DESC"
    packing_master_data = await db_conn_all(packing_master)
    return await render_template("packing_summary.html", data=packing_master_data)


@app.route("/manual_box_id", methods=["POST"])
async def manual_box_id():
    operator_name_manual = request.args.get("operator_name")
    group_type_manual = request.args.get("group_type")

    data = await request.get_json()
    packing_box_id = data.get("packing_box_id")

    if packing_box_id.startswith(box_start) and len(packing_box_id) == box_len:
        box_id = packing_box_id
        top_box_sql = f"SELECT 1 FROM H66_PACKING_MASTER WHERE box_id = '{box_id}'"
        top_box_row = await db_conn_one(top_box_sql)

        if top_box_row:
            print(f"Box ID {box_id} is duplicate")
            messages.append(
                {"type": "error", "message": f"Box ID {box_id} is duplicate"}
            )
            logging.info(f"Box ID {box_id} is duplicate")
        else:
            box_id_query = "SELECT box_id FROM H66_PACKING_MASTER WHERE status is null"
            box_id_row = await db_conn_one(box_id_query)
            if box_id_row:
                box_id = box_id_row[0]
                print(f"Complete the existing box {box_id}")
                messages.append(
                    {"type": "error", "message": f"Complete the existing box {box_id}"}
                )
                logging.info(f"Complete the existing box {box_id}")

            else:
                zero = 0
                current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                insert_query = (
                    f"INSERT INTO H66_PACKING_MASTER (box_id, date_time, group_type, part_qty, operator_name) VALUES "
                    f"('{box_id}', '{current_datetime}', '{group_type_manual}',"
                    f"'{zero}','{operator_name_manual}')"
                )
                await db_conn_commit(insert_query)
                print(f"Box ID {box_id} accepted and saved")
                messages.append(
                    {
                        "type": "success",
                        "message": f"Box ID {box_id} accepted and saved",
                    }
                )
                logging.info(f"Box ID {box_id} accepted and saved")

    elif packing_box_id:
        print(
            "Please scan Box ID before scanning part OR Box ID is not in proper format"
        )
        messages.append(
            {
                "type": "error",
                "message": "Please scan Box ID before scanning part OR Box ID is not in proper format",
            }
        )
        logging.info(
            "Please scan Box ID before scanning part OR Box ID is not in proper format"
        )

    return redirect(url_for("packing_scan"))


@app.route("/packing_scan", methods=["POST", "GET"])
@login_required
async def packing_scan():
    operator_name = request.args.get("operator_name")
    group_type = request.args.get("group_type")

    async def serial_worker():
        while True:
            box_id = None

            # serial_read = input('Enter the value you want')
            if ser.in_waiting:
                serial_read = ser.readline().strip().decode("utf-8")
                print(f"Received Data:{serial_read}; {len(serial_read)}")
                logging.info(f"Received Data:{serial_read}; {len(serial_read)}")

                last_box_sql = "SELECT box_id, group_type FROM H66_PACKING_MASTER WHERE status is null"
                box_details = await db_conn_one(last_box_sql)

                if box_details:
                    box_id = box_details[0]
                    print("this is the", box_id)
                    logging.info(f"this is the {box_id}")

                part_counter = await count_part_dual_motor(box_id)
                if part_counter < 228:
                    if (
                        serial_read.startswith(box_start)
                        and len(serial_read) == box_len
                    ):
                        box_id = serial_read
                        top_box_sql = f"SELECT 1 FROM H66_PACKING_MASTER WHERE box_id = '{box_id}'"
                        top_box_row = await db_conn_one(top_box_sql)

                        if top_box_row:
                            print(f"Box ID {box_id} is duplicate")
                            messages.append(
                                {
                                    "type": "error",
                                    "message": f"Box ID {box_id} is duplicate",
                                }
                            )
                            logging.info(f"Box ID {box_id} is duplicate")

                        else:
                            box_id_query = "SELECT box_id FROM H66_PACKING_MASTER WHERE status is null"
                            box_id_row = await db_conn_one(box_id_query)
                            if box_id_row:
                                box_id = box_id_row[0]
                                print(f"Complete the existing box {box_id}")
                                messages.append(
                                    {
                                        "type": "error",
                                        "message": f"Complete the existing box {box_id}",
                                    }
                                )
                                logging.info(f"Complete the existing box {box_id}")

                            else:
                                zero = 0
                                current_datetime = datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )
                                insert_query = (
                                    f"INSERT INTO H66_PACKING_MASTER (box_id, date_time, group_type, part_qty, operator_name) VALUES "
                                    f"('{box_id}', '{current_datetime}', '{group_type}',"
                                    f"'{zero}','{operator_name}')"
                                )
                                await db_conn_commit(insert_query)
                                print(f"Box ID {box_id} accepted and saved")
                                messages.append(
                                    {
                                        "type": "success",
                                        "message": f"Box ID {box_id} accepted and saved",
                                    }
                                )
                                logging.info(f"Box ID {box_id} accepted and saved")

                    elif box_id is None:
                        print(
                            "Please scan Box ID before scanning part OR Box ID is not in proper format"
                        )
                        messages.append(
                            {
                                "type": "error",
                                "message": "Please scan Box ID before scanning part OR Box ID is not in proper format",
                            }
                        )
                        logging.info("Please scan Box ID before scanning part OR Box ID is not in proper format")

                    elif (
                        serial_read.startswith(part_starts)
                        and len(serial_read) == part_len
                    ):
                        part_id = serial_read
                        part_sql = f"SELECT 1 FROM H66_PACKING_PART_MASTER WHERE part_id = '{part_id}'"
                        part_id_res = await db_conn_one(part_sql)

                        check_group_type_multiguage = await group_type_check(part_id)
                        H66_1_GRT = await status_H66_1_GRT(part_id)
                        H66_1_MULTIGAUGING = await status_H66_1_MULTIGAUGING(part_id)
                        H66_2_GRT = await status_H66_2_GRT(part_id)
                        H66_2_MULTIGAUGING = await status_H66_2_MULTIGAUGING(part_id)
                        honing_type, dresser_id = await get_honing_type(part_id)

                        print(
                            f"H66_1_GRT: {H66_1_GRT}, H66_2_GRT: {H66_2_GRT}, M_1: {H66_1_MULTIGAUGING}, M_2: {H66_2_MULTIGAUGING}"
                        )

                        if part_id_res:
                            print(f"The Part ID {part_id} is duplicate")
                            messages.append(
                                {
                                    "type": "error",
                                    "message": f"The Part ID {part_id} is duplicate",
                                }
                            )
                            logging.info(f"The Part ID {part_id} is duplicate")

                        elif group_type == "C":
                            if honing_type is None:
                                print("Please scan on Honing Machine First")
                                messages.append(
                                    {
                                        "type": "error",
                                        "message": "Please scan on Honing Machine First",
                                    }
                                )
                                logging.info("Please scan on Honing Machine First")
                            elif (
                                H66_1_MULTIGAUGING == "ACCEPT"
                                or H66_2_MULTIGAUGING == "ACCEPT"
                            ):
                                zunkar_bool = await junkar_part_check(part_id)
                                current_datetime_part = datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )
                                insert_query = f"""INSERT INTO H66_PACKING_PART_MASTER 
                                    (part_id, box_id, date_time, honing_type, honing_dresser_id, od_machine) 
                                    VALUES ('{part_id}', '{box_id}', '{current_datetime_part}', 
                                    '{honing_type}', '{dresser_id}','{zunkar_bool}') """

                                await db_conn_commit(insert_query)
                                print(f"The Part ID {part_id} accepted and saved")
                                messages.append(
                                    {
                                        "type": "success",
                                        "message": f"The Part ID {part_id} accepted and saved",
                                    }
                                )
                            logging.info(f"The Part ID {part_id} accepted and saved")
                        elif (
                            H66_1_GRT is None
                            and H66_2_GRT is None
                            and H66_1_MULTIGAUGING is None
                            and H66_2_MULTIGAUGING is None
                            and multi_set == "True"
                        ):
                            print(
                            f"Part ID {part_id} is pending for scan on either of the GRT and either of the Multiguage"
                            )
                            messages.append(
                                {
                                    "type": "error",
                                    "message": f"Part ID {part_id} is pending for scan on either of the GRT and either of the Multiguage",
                                }
                            )
                            logging.info(f"Part ID {part_id} is pending for scan on either of the GRT and either of the Multiguage")

                        elif (
                                check_group_type_multiguage is None
                                and multi_set == "True"):
                            print("No group type has been identified")
                            messages.append(
                                {
                                    "type": "error",
                                    "message": "No group type has been identified",
                                }
                            )
                            logging.info("No group type has been identified")
                        elif (
                            check_group_type_multiguage != group_type
                            and multi_set == "True"
                        ):
                            print(
                                f"Group Type is '{group_type}' but '{check_group_type_multiguage}' has been scanned"
                            )
                            messages.append(
                                {
                                    "type": "error",
                                    "message": f"Group Type is '{group_type}' but '{check_group_type_multiguage}' has been scanned",
                                }
                            )
                            logging.info(
                                f"Group Type is '{group_type}' but '{check_group_type_multiguage}' has been scanned"
                            )
                        elif (
                            H66_1_GRT is None
                            and H66_2_GRT is None
                            and multi_set == "True"
                        ):
                            print(
                                f"Pending status on H66_1_GRT or H66_2_GRT for Part id {part_id}"
                            )
                            messages.append(
                                {
                                    "type": "error",
                                    "message": f"Pending status in H66_1_GRT for Part id {part_id}",
                                }
                            )
                            logging.info(
                                f"Pending status in H66_1_GRT for Part id {part_id}"
                            )
                        elif (
                            H66_1_MULTIGAUGING is None
                            and H66_2_MULTIGAUGING is None
                            and multi_set == "True"
                        ):
                            print(
                                f"Pending status in H66_1_MULTIGAUGING or H66_2_MULTIGAUGING for Part id {part_id}"
                            )
                            messages.append(
                                {
                                    "type": "error",
                                    "message": f"Pending status in H66_1_MULTIGAUGING or H66_2_MULTIGAUGING for Part id {part_id}",
                                }
                            )
                            logging.info(
                                f"Pending status in H66_1_MULTIGAUGING or H66_2_MULTIGAUGING for Part id {part_id}"
                            )
                        elif H66_1_GRT == "REJECT" and H66_2_GRT == "REJECT":
                            print(f"Part id {part_id} is rejected on both GRTs")
                            messages.append(
                                {
                                    "type": "error",
                                    "message": f"Part id {part_id} is rejected on both GRTs",
                                }
                            )
                            logging.info(f"Part id {part_id} is rejected on both GRTs")
                        elif (
                            H66_1_MULTIGAUGING == "REJECT"
                            and H66_2_MULTIGAUGING == "REJECT"
                        ):
                            print(f"Part id {part_id} is rejected on both multigauges")
                            messages.append(
                                {
                                    "type": "error",
                                    "message": f"Part id {part_id} is rejected on both multigauges",
                                }
                            )
                            logging.info(
                                f"Part id {part_id} is rejected on both multigauges"
                            )
                        elif (H66_1_GRT == "REJECT" and H66_2_GRT == "REJECT") and (
                            H66_1_MULTIGAUGING == "REJECT"
                            and H66_2_MULTIGAUGING == "REJECT"
                        ):
                            print(
                                f"Part ID {part_id} is rejected on both GRTs and both multigauges"
                            )
                            messages.append(
                                {
                                    "type": "error",
                                    "message": f"Part id {part_id} is rejected on both GRTs and both multigauges",
                                }
                            )
                            logging.info(
                                f"Part ID {part_id} is rejected on both GRTs and both multigauges"
                            )
                        elif (H66_1_GRT is None and H66_2_GRT == "ACCEPT") and (
                            H66_1_MULTIGAUGING is None
                            and H66_2_MULTIGAUGING == "REJECT"
                        ):
                            print(f"Part ID {part_id} is rejected on H66_2_MULTIGUAGE")
                            messages.append(
                                {
                                    "type": "error",
                                    "message": f"Part id {part_id} is rejected on H66_2_MULTIGUAGE",
                                }
                            )
                            logging.info(
                                f"Part ID {part_id} is rejected on H66_2_MULTIGUAGE"
                            )
                        elif (H66_1_GRT is None and H66_2_GRT == "REJECT") and (
                            H66_1_MULTIGAUGING is None
                            and H66_2_MULTIGAUGING == "ACCEPT"
                        ):
                            print(f"Part ID {part_id} is rejected on H66_2_GRT")
                            messages.append(
                                {
                                    "type": "error",
                                    "message": f"Part ID {part_id} is rejected on H66_2_GRT",
                                }
                            )
                            logging.info(f"Part ID {part_id} is rejected on H66_2_GRT")
                        elif (H66_1_GRT == "ACCEPT" and H66_2_GRT is None) and (
                            H66_1_MULTIGAUGING == "REJECT"
                            and H66_2_MULTIGAUGING is None
                        ):
                            print(
                                f"Part ID {part_id} is rejected on H66_1_MULTIGUAGING"
                            )
                            messages.append(
                                {
                                    "type": "error",
                                    "message": f"Part ID {part_id} is rejected on H66_1_MULTIGUAGING",
                                }
                            )
                            logging.info(
                                f"Part ID {part_id} is rejected on H66_1_MULTIGUAGING"
                            )
                        elif (H66_1_GRT == "REJECT" and H66_2_GRT is None) and (
                            H66_1_MULTIGAUGING == "ACCEPT"
                            and H66_2_MULTIGAUGING is None
                        ):
                            print(f"Part ID {part_id} is rejected on H66_1_GRT")
                            messages.append(
                                {
                                    "type": "error",
                                    "message": f"Part ID {part_id} is rejected on H66_1_GRT",
                                }
                            )
                            logging.info(f"Part ID {part_id} is rejected on H66_1_GRT")
                        elif (H66_1_GRT == "REJECT" and H66_2_GRT is None) and (
                            H66_1_MULTIGAUGING == "REJECT"
                            and H66_2_MULTIGAUGING is None
                        ):
                            print(
                                f"Part ID {part_id} is rejected on both H66_1_GRT and H66_1_MULTIGAUGING"
                            )
                            messages.append(
                                {
                                    "type": "error",
                                    "message": f"Part ID {part_id} is rejected on both H66_1_GRT and H66_1_MULTIGAUGING",
                                }
                            )
                            logging.info(
                                f"Part ID {part_id} is rejected on both H66_1_GRT and H66_1_MULTIGAUGING"
                            )
                        elif (H66_1_GRT is None and H66_2_GRT == "REJECT") and (
                            H66_1_MULTIGAUGING is None
                            and H66_2_MULTIGAUGING == "REJECT"
                        ):
                            print(
                                f"Part ID {part_id} is rejected on both H66_2_GRT and H66_2_MULTIGAUGING"
                            )
                            messages.append(
                                {
                                    "type": "error",
                                    "message": f"Part ID {part_id} is rejected on both H66_2_GRT and H66_2_MULTIGAUGING",
                                }
                            )
                            logging.info(
                                f"Part ID {part_id} is rejected on both H66_2_GRT and H66_2_MULTIGAUGING"
                            )
                        elif honing_type is None:
                            print("Please scan on Honing Machine First")
                            messages.append(
                                {
                                    "type": "error",
                                    "message": "Please scan on Honing Machine First",
                                }
                            )
                            logging.info("Please scan on Honing Machine First")
                        else:
                            part_counter += 1
                            if part_counter == 1:
                                if part_id:
                                    rev_no = part_id[11:13]
                                    update_revno_query = f"UPDATE H66_PACKING_MASTER SET rev_no = '{rev_no}' WHERE box_id = '{box_id}'"
                                    await db_conn_commit(update_revno_query)
                            else:
                                print(part_counter)
                                logging.info(part_counter)
                            current_datetime_part = datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )

                            zunkar_bool = await junkar_part_check(part_id)
                            insert_query = (
                                f"""INSERT INTO H66_PACKING_PART_MASTER 
                                (part_id, box_id, date_time, honing_type, honing_dresser_id, od_machine) 
                                VALUES ('{part_id}', '{box_id}', '{current_datetime_part}',
                                 '{honing_type}', '{dresser_id}', '{zunkar_bool}') """
                            )
                            await db_conn_commit(insert_query)
                            print(f"The Part ID {part_id} accepted and saved")
                            messages.append(
                                {
                                    "type": "success",
                                    "message": f"The Part ID {part_id} accepted and saved",
                                }
                            )
                            logging.info(f"The Part ID {part_id} accepted and saved")
                            if part_counter == 228:
                                update_query_box_full = (
                                    f"UPDATE H66_PACKING_MASTER SET part_qty = '{part_counter}' "
                                    f"WHERE box_id = '{box_id}'"
                                )
                                await db_conn_commit(update_query_box_full)
                                print(
                                    f"The Box ID {box_id} is full. Please save the data"
                                )
                                messages.append(
                                    {
                                        "type": "success",
                                        "message": f"The Box ID {box_id} is full. Please save the data",
                                    }
                                )
                                logging.info(
                                    f"The Box ID {box_id} is full. Please save the data"
                                )

                                break
                            else:
                                print("Continue scanning")
                                logging.info("Continue Scanning")
                    else:
                        print(f"Part ID not in proper format")
                        messages.append(
                            {"type": "error", "message": "Part ID not in proper format"}
                        )

                else:
                    print("Box is full. Please use a new box")
                    messages.append(
                        {
                            "type": "error",
                            "message": "Box is full. Please use a new box",
                        }
                    )
                    logging.info("Box is full. Please use a new box")
                    break

    threading.Thread(target=asyncio.run, args=(serial_worker(),), daemon=True).start()

    # query for getting the last box id
    last_box_sql = """SELECT TOP 1 box_id, part_qty 
                      FROM H66_PACKING_MASTER WHERE status is null
                      ORDER BY date_time DESC"""

    last_box_res = await db_conn_one(last_box_sql)

    # error handling part if the last_box_res does not exist
    if not last_box_res:
        box_id = None
        scan_date = None
        rev_no1 = None
        part_data = []
        logging.info("Scan a box id to continue")
    else:
        box_id = last_box_res[0]

        # all part data for the box id
        part_data_sql = f"""
            SELECT date_time, part_id, honing_type, od_machine
            FROM H66_PACKING_PART_MASTER
            WHERE box_id = '{box_id}'
            ORDER BY date_time DESC
            OFFSET 1 ROWS
        """

        part_rows = await db_conn_all(part_data_sql)

        part_data = []
        if part_rows:
            for rows in part_rows:
                part_data.append(
                    {
                        "date_time": rows[0],
                        "part_id": rows[1],
                        "honing_type": rows[2],
                        "od_machine": rows[3],
                    }
                )
        else:
            part_data = []

        # box id details
        all_data_sql = f"""
            SELECT box_id, date_time, rev_no, operator_name
            FROM H66_PACKING_MASTER
            WHERE box_id='{box_id}'
            ORDER BY date_time ASC
            """
        all_data = await db_conn_one(all_data_sql)
        print(all_data)

        if all_data:
            box_id = all_data[0]
            scan_date = all_data[1]
            rev_no1 = all_data[2]
            operator_name = all_data[3]
        else:
            print("No data found for the specified box_id")
            logging.info("No data found for the specified box_id")
            scan_date = rev_no1 = box_id = None

    return await render_template(
        "packing_scan.html",
        box_id=box_id,
        group_type=group_type,
        scan_date=scan_date,
        rev_no=rev_no1,
        part_data=part_data,
        operator_name=operator_name,
    )


@app.route("/data_part", methods=["POST", "GET"])
@login_required
async def data_part():
    last_box_sql = """SELECT TOP 1 box_id, part_qty 
                    FROM H66_PACKING_MASTER where STATUS is null ORDER BY date_time DESC"""
    last_box_res = await db_conn_one(last_box_sql)

    if not last_box_res:
        return jsonify({"success": "No box with sufficient parts found."}), 200

    box_id = last_box_res[0]
    tri_box_sql = f"SELECT 1 FROM H66_PACKING_PART_MASTER WHERE box_id = '{box_id}'"
    tri_box_res = await db_conn_one(tri_box_sql)

    if tri_box_res is not None:
        rt_update_sql = f"""
                        SELECT TOP 1 part_id, box_id, date_time, honing_type, od_machine,
                            (SELECT COUNT(*) FROM H66_PACKING_PART_MASTER WHERE box_id = PM.box_id) AS total_part_count
                        FROM H66_PACKING_PART_MASTER PM
                        WHERE box_id = '{box_id}'
                        ORDER BY date_time DESC
                    """
        rt_update = await db_conn_all(rt_update_sql)

        if not rt_update:
            return jsonify({"success": "No part data found for the selected box."}), 200

        rt_part = []
        for parts in rt_update:
            parts = list(parts)
            date_time = parts[2]

            if isinstance(date_time, str):
                date_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")

            parts[2] = date_time.strftime("%Y-%m-%d %H:%M:%S")

            row_headers = [
                "PART_ID",
                "BOX_ID",
                "DATE_TIME",
                "honing_type",
                "od_machine",
                "total_part_count",
            ]
            rt_part.append(dict(zip(row_headers, parts)))
        return jsonify(rt_part)
    else:
        rt_update_sql = f"""
                        SELECT TOP 1 part_id, box_id, date_time, honing_type, od_machine,
                            (SELECT COUNT(*) FROM H66_PACKING_PART_MASTER WHERE box_id = PM.box_id) AS total_part_count
                        FROM H66_PACKING_PART_MASTER PM
                        WHERE box_id = '{box_id}'
                        ORDER BY date_time DESC
                    """
        rt_update = await db_conn_all(rt_update_sql)

        if not rt_update:
            return jsonify({"success": "No part data found for the selected box."}), 200

        rt_part = []
        for parts in rt_update:
            parts = list(parts)
            date_time = parts[2]

            if isinstance(date_time, str):
                date_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")

            parts[2] = date_time.strftime("%Y-%m-%d %H:%M:%S")

            row_headers = [
                "PART_ID",
                "BOX_ID",
                "DATE_TIME",
                "honing_type",
                "od_machine",
                "total_part_count",
            ]
            rt_part.append(dict(zip(row_headers, parts)))

        return jsonify(rt_part)


async def send_email_with_attachment(
    data_part_master, box_id, group_type, rev_no, part_counter, operator_name, date_time
):
    smtp_server = "exchsrv.kalyanicorp.com"
    PORT = 587

    sender_email = "Helpdesk.KTSL@kalyanitechnoforge.com"
    sender_password = "dktf@00019"
    username = "dktf00019@kalyanitfl.com"

    # recipient addresses
    with open("recipients.txt", "r") as file:
        recipients = [line.strip() for line in file]

    # CC addresses
    with open("cc_recipients.txt", "r") as file:
        cc_recipients = [line.strip() for line in file]

    message = MIMEMultipart()
    message["Subject"] = f"H66 Packed Box {box_id}"
    message["From"] = sender_email
    message["To"] = ", ".join(recipients)
    message["Cc"] = ", ".join(cc_recipients)

    text = "Please find the attached report with the data."
    text_part = MIMEText(text, "plain")
    message.attach(text_part)

    html_content = await render_template(
        "H66_template.html",
        part_master=data_part_master,
        box_id=box_id,
        group_type=group_type,
        rev_no=rev_no,
        part_counter=part_counter,
        operator_name=operator_name,
        date_time=date_time,
    )

    # Create a filename using the box number
    attachment_filename = f"{box_id}.html"
    attachment_path = os.path.join("Packed Box", attachment_filename)

    # Save the rendered template to a uniquely named file
    async with aio_open(attachment_path, "w") as file:
        await file.write(html_content)

    # Attach the HTML file
    if os.path.isfile(attachment_path):
        try:
            async with aio_open(attachment_path, "rb") as attachment_file:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(await attachment_file.read())

                encoders.encode_base64(part)

                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(attachment_path)}",
                )
                message.attach(part)
        except Exception as e:
            print(f"Error reading or attaching the file: {e}")
            logging.info(f"Error reading or attaching the file: {e}")
            return
    else:
        print(f"Error: File {attachment_path} not found.")
        logging.info(f"Error: File {attachment_path} not found.")
        return

    try:
        await aiosmtplib.send(
            message,
            hostname=smtp_server,
            port=PORT,
            start_tls=True,
            username=username,
            password=sender_password,
        )
        print("[*] Email sent successfully.")
        logging.info("[*] Email sent successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        logging.info(f"An error occurred: {e}")


@app.route("/save", methods=["POST", "GET"])
@login_required
async def save():
    last_dresser_sql = """SELECT TOP 1 box_id, rev_no, group_type, date_time, operator_name
                          FROM H66_PACKING_MASTER WHERE
                          STATUS IS NULL ORDER BY DATE_TIME DESC"""

    last_dresser_res = await db_conn_one(last_dresser_sql)

    data_part_master = []
    if last_dresser_res:
        box_id = last_dresser_res[0]
        rev_no = last_dresser_res[1]
        group_type = last_dresser_res[2]
        box_date_time = last_dresser_res[3]
        operator_name = last_dresser_res[4]

        part_count_sql = f"""SELECT 
                        (SELECT COUNT(part_id) FROM H66_PACKING_PART_MASTER WHERE box_id = '{box_id}') AS total_count, 
                        part_id, honing_type, od_machine, honing_dresser_id
                        FROM H66_PACKING_PART_MASTER
                        WHERE box_id = '{box_id}'"""

        part_count_res = await db_conn_all(part_count_sql)

        for i in range(0, len(part_count_res)):
            part_id = part_count_res[i][1]
            honing_type = part_count_res[i][2]
            od_machine = part_count_res[i][3]
            honing_dresser_id = part_count_res[i][4]

            part_data = next(
                (item for item in data_part_master if item["part_id"] == part_id), None
            )
            if not part_data:
                part_data = {
                    "part_id": part_id,
                    "honing_type": honing_type,
                    "od_machine": od_machine,
                    "honing_dresser_id": honing_dresser_id,
                }
                data_part_master.append(part_data)

            # GRT search logic
            search_grt_1 = f"""SELECT TOP 1 result_id, time_stamp, d3,d5,d6,d7,d8,d9 FROM [24M1570200_H66_1_GRT] 
                                WHERE part_nbr = '{part_id}' 
                                ORDER BY TIME_STAMP DESC"""
            grt_1_res = await db_conn_all(search_grt_1)

            if not grt_1_res:
                search_grt_2 = f"""SELECT TOP 1 result_id, time_stamp, d3,d5,d6,d7,d8,d9 FROM [24M1570100_H66_2_GRT] 
                                   where part_nbr = '{part_id}' 
                                   ORDER BY TIME_STAMP DESC"""
                grt_2_res = await db_conn_all(search_grt_2)
                part_data["GRT_Status"] = grt_2_res[0][0]
                part_data["GRT_Scanning_Time"] = grt_2_res[0][1]
                part_data["GRT_D3"] = grt_2_res[0][2]
                part_data["GRT_D5"] = grt_2_res[0][3]
                part_data["GRT_D6"] = grt_2_res[0][4]
                part_data["GRT_D7"] = grt_2_res[0][5]
                part_data["GRT_D8"] = grt_2_res[0][6]
                part_data["GRT_D9"] = grt_2_res[0][7]
            else:
                part_data["GRT_Status"] = grt_1_res[0][0]
                part_data["GRT_Scanning_Time"] = grt_1_res[0][1]
                part_data["GRT_D3"] = grt_1_res[0][2]
                part_data["GRT_D5"] = grt_1_res[0][3]
                part_data["GRT_D6"] = grt_1_res[0][4]
                part_data["GRT_D7"] = grt_1_res[0][5]
                part_data["GRT_D8"] = grt_1_res[0][6]
                part_data["GRT_D9"] = grt_1_res[0][7]

            # Multiguage search logic
            search_multiguage_1 = f"""SELECT TOP 1 result_id, time_stamp, d1,d2,d5,d6,d8,d10,d11,d12,
                                    d16,d17,d20,d21,d22,d23,d24,d25,d26,d27,d28   
                                    FROM [24M1570200_H66_1_MULTIGAUGING]  
                                    WHERE part_nbr = '{part_id}' 
                                    ORDER BY TIME_STAMP DESC"""

            multiguage_1_res = await db_conn_all(search_multiguage_1)

            if not multiguage_1_res:
                search_multiguage_2 = f"""SELECT TOP 1 result_id, time_stamp, d1,d2,d5,d6,d8,d10,d11,d12,
                                    d16,d17,d20,d21,d22,d23,d24,d25,d26,d27,d28
                                    FROM [24M1570100_H66_2_MULTIGAUGING]  
                                    WHERE part_nbr = '{part_id}' 
                                    ORDER BY TIME_STAMP DESC"""

                multiguage_2_res = await db_conn_all(search_multiguage_2)

                part_data["Multiguage_Status"] = multiguage_2_res[0][0]
                part_data["Multigauging_Scanning_Time"] = multiguage_2_res[0][1]
                part_data["D1"] = multiguage_2_res[0][2]
                part_data["D2"] = multiguage_2_res[0][3]
                part_data["D5"] = multiguage_2_res[0][4]
                part_data["D6"] = multiguage_2_res[0][5]
                part_data["D8"] = multiguage_2_res[0][6]
                part_data["D10"] = multiguage_2_res[0][7]
                part_data["D11"] = multiguage_2_res[0][8]
                part_data["D12"] = multiguage_2_res[0][9]
                part_data["D16"] = multiguage_2_res[0][10]
                part_data["D17"] = multiguage_2_res[0][11]
                part_data["D20"] = multiguage_2_res[0][12]
                part_data["D21"] = multiguage_2_res[0][13]
                part_data["D22"] = multiguage_2_res[0][14]
                part_data["D23"] = multiguage_2_res[0][15]
                part_data["D24"] = multiguage_2_res[0][16]
                part_data["D25"] = multiguage_2_res[0][17]
                part_data["D26"] = multiguage_2_res[0][18]
                part_data["D27"] = multiguage_2_res[0][19]
                part_data["D28"] = multiguage_2_res[0][20]
            else:
                part_data["Multiguage_Status"] = multiguage_1_res[0][0]
                part_data["Multigauging_Scanning_Time"] = multiguage_1_res[0][1]
                part_data["D1"] = multiguage_1_res[0][2]
                part_data["D2"] = multiguage_1_res[0][3]
                part_data["D5"] = multiguage_1_res[0][4]
                part_data["D6"] = multiguage_1_res[0][5]
                part_data["D8"] = multiguage_1_res[0][6]
                part_data["D10"] = multiguage_1_res[0][7]
                part_data["D11"] = multiguage_1_res[0][8]
                part_data["D12"] = multiguage_1_res[0][9]
                part_data["D16"] = multiguage_1_res[0][10]
                part_data["D17"] = multiguage_1_res[0][11]
                part_data["D20"] = multiguage_1_res[0][12]
                part_data["D21"] = multiguage_1_res[0][13]
                part_data["D22"] = multiguage_1_res[0][14]
                part_data["D23"] = multiguage_1_res[0][15]
                part_data["D24"] = multiguage_1_res[0][16]
                part_data["D25"] = multiguage_1_res[0][17]
                part_data["D26"] = multiguage_1_res[0][18]
                part_data["D27"] = multiguage_1_res[0][19]
                part_data["D28"] = multiguage_1_res[0][20]

        if part_count_res:
            part_count1 = part_count_res[0][0]

            if request.method == "POST" and part_count1 == 228:
                await send_email_with_attachment(
                    data_part_master,
                    box_id,
                    group_type,
                    rev_no,
                    part_count1,
                    operator_name,
                    box_date_time,
                )
                update_dresser_master = f"""UPDATE H66_PACKING_MASTER SET status = 1, part_qty = '{part_count1}'
                                            WHERE box_id = '{box_id}'"""
                await db_conn_commit(update_dresser_master)
                return redirect(url_for("packing_selection"))
            else:
                return redirect(url_for("packing_scan"))
        else:
            messages.append(
                {
                    "type": "error",
                    "message": "Some error occurred while saving the data.",
                }
            )
            logging.info("The packing data is empty")
            return redirect(url_for("packing_scan"))
    else:
        return redirect(url_for("packing_scan"))


@app.route("/delete-part", methods=["POST"])
@login_required
async def delete_part():
    data = await request.get_json()
    part_id = data["part_id"]
    print(data)

    last_box_sql = """SELECT TOP 1 box_id, group_type, part_qty
                    FROM H66_PACKING_MASTER where status is null 
                    ORDER BY date_time DESC"""
    box_details = await db_conn_one(last_box_sql)

    if box_details:
        box_id = box_details[0]

        part_counter = await count_part_dual_motor(box_id)
        if part_counter == 1:
            try:
                # Update H66_PACKING_MASTER table to set part1_type and part2_type as null
                update_sql = (
                    f"UPDATE H66_PACKING_MASTER SET rev_no=Null WHERE box_id='{box_id}'"
                )
                await db_conn_commit(update_sql)

                # Delete the part from H66_PACKING_PART_MASTER table
                del_sql = (
                    f"DELETE FROM H66_PACKING_PART_MASTER WHERE PART_ID='{part_id}'"
                )
                await db_conn_commit(del_sql)

                print(f"Part ID {part_id} successfully deleted")
                messages.append(
                    {
                        "type": "success",
                        "message": {
                            "type": "success",
                            "message": f"Part ID {part_id} successfully deleted",
                        },
                    }
                )
                return jsonify({"success": True})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)})
        elif part_counter == 5:
            try:
                # Update H66_PACKING_MASTER table to set part_qty
                update_sql = (
                    f"UPDATE H66_PACKING_MASTER SET part_qty=0 WHERE box_id='{box_id}'"
                )
                await db_conn_commit(update_sql)

                # Delete the part from H66_PACKING_PART_MASTER table
                del_sql = (
                    f"DELETE FROM H66_PACKING_PART_MASTER WHERE PART_ID='{part_id}'"
                )
                await db_conn_commit(del_sql)

                print(f"Part ID {part_id} successfully deleted")
                messages.append(
                    {
                        "type": "success",
                        "message": f"Part ID {part_id} successfully deleted",
                    }
                )
                logging.info(f"Part ID {part_id} successfully deleted")
                return jsonify({"success": True})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)})
        else:
            try:
                # Delete the part from H66_PACKING_PART_MASTER table
                del_sql = (
                    f"DELETE FROM H66_PACKING_PART_MASTER WHERE PART_ID='{part_id}'"
                )
                await db_conn_commit(del_sql)

                print(f"Part ID {part_id} successfully deleted")
                messages.append(
                    {
                        "type": "success",
                        "message": f"Part ID {part_id} successfully deleted",
                    }
                )
                logging.info(f"Part ID {part_id} successfully deleted")
                return jsonify({"success": True})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)})


@app.route("/delete-box", methods=["POST"])
@login_required
async def delete_box():
    try:
        data = await request.get_json()
        del_box_id = data["box_id"]
        print(data)

        if del_box_id != "None":
            # query for deleting the part_id from dresser_part_master
            delete_dresser_part_sql = (
                f"DELETE FROM H66_PACKING_PART_MASTER WHERE box_id = '{del_box_id}'"
            )
            await db_conn_commit(delete_dresser_part_sql)

            # query for deleting the dresser id from dresser_master table
            delete_dresser_sql = (
                f"DELETE FROM H66_PACKING_MASTER WHERE box_id = '{del_box_id}'"
            )
            await db_conn_commit(delete_dresser_sql)
            return jsonify(
                {"success": False, "error": f"Box ID '{del_box_id}' deleted"}
            )
        else:
            return jsonify({"success": False, "error": "You cannot delete a NONE id."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5070")
    app.run(debug=True, port=5070, use_reloader=False)
