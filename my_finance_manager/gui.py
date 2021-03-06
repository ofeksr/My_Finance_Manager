import re
import tkinter as tk
from glob import glob
from tkinter import ttk, messagebox, simpledialog

from PIL import ImageTk, Image
from tkinterhtml import HtmlFrame

from exceptions import logging, datetime
from mfm import MyFinanceManager
from scrapers.meitav_dash_scraper import get_trader_info
from scrapers.otsar_hahayal_scraper import get_bank_info
from tools.calculator import Calculator


class Application(MyFinanceManager, tk.Frame):
    LOGO = 'media/gui/MFM-logo.jpg'
    LOG = logging.getLogger('MFM.GUI.Logger')
    EXAMPLE_FORM = 'media/gui/example_form.jpg'

    portfolio = None
    save_flag = False  # flag for quit without saving message on closing root window.

    def __init__(self, parent=None):
        """Creating all widgets and menu bar."""
        self.LOG.debug('Initializing MFM GUI object')

        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.menu_bar = tk.Menu(parent)
        root.config(menu=self.menu_bar)

        self.assets_info = self.assets_lbl()

        self.root_background = self.root_bg()

        self.all_in_one_btn, self.progress_lbl = self.create_aio_btn()

        self.progress_lbl_mode(process=True)  # indicating in process mode

        self.active_window(window=root, is_root=True)

        self.file = self.file_menu()
        self.edit = self.edit_menu()
        self.view = self.view_menu()
        self.graphs = self.graphs_menu()
        self.tools = self.tools_menu()
        self.help_m = self.help_menu()

        self.last_update_info, self.email_info = self.bottom_bar()

        self.load_portfolio()

        self.root_binds()

        self.progress_lbl_mode()  # indicating idle mode

        self.LOG.info('MFM GUI object created successfully')

    ##############################################################################################

    def assets_lbl(self):
        self.LOG.debug('Creating assets label')
        txt = tk.Label(root, text='\n')
        txt.pack(side='top', fill='x')
        return txt

    def progress_lbl_mode(self, process: bool = False):
        self.LOG.debug(f'Changing progress label, process={process}')
        if process:
            self.progress_lbl.configure(text='Processing..', fg='red')
            root.update_idletasks()
            root.after(200)
        else:
            self.progress_lbl.configure(text='Idle', fg='black')

    def root_bg(self):
        self.LOG.debug('Applying root window background')
        photo = ImageTk.PhotoImage(Image.open(self.LOGO))
        lbl_bg = tk.Label(root, image=photo)
        lbl_bg.image = photo
        lbl_bg.pack(side='top', fill="both", expand="yes")
        return lbl_bg

    def create_top_level(self, title: str = None, geometry: str = None):
        """init for creating top level windows"""
        self.LOG.debug(f'Creating top level window [title={title}, geometry={geometry}]')
        if geometry is None:
            geometry = '350x200'
        top = tk.Toplevel()
        top.title(title)
        if geometry:
            top.geometry(geometry)
        self.active_window(window=top)
        return top

    def bottom_bar(self, last_update: list = None):
        """creating and updating bottom bar info"""

        if last_update:
            self.LOG.debug('Changing bottom bar info')

            self.last_update_info.configure(text='Last Updated: Stocks - {0},'
                                                 ' Bank Cash Flow - {1}, Trader Cash Flow - {2}'
                                            .format(*last_update))
            self.email_info.configure(text=f'Email Address: {self.portfolio.db.user_info.get_user_email_address()}')

        else:
            self.LOG.debug('Creating bottom bar info widget')
            lbl_f1 = tk.LabelFrame(root)
            lbl_f1.pack(side='bottom', anchor='sw', fill='x')

            lbl_update_dates = tk.Label(lbl_f1, text='Last Updated: Stocks - None, Bank & Trader Cash Flow - None')
            lbl_update_dates.pack(side='bottom', anchor='sw')

            lbl_f3 = tk.LabelFrame(root)
            lbl_f3.pack(side='bottom', anchor='sw', fill='x')

            lbl_email_a = tk.Label(lbl_f3, text=f'Email Address: None')
            lbl_email_a.pack(side='bottom', anchor='sw')

            return lbl_update_dates, lbl_email_a

    def create_aio_btn(self):
        self.LOG.debug('Creating AIO button and progress label')
        lbl_f = tk.LabelFrame(self.root_background)
        lbl_f.pack(side='bottom', anchor='sw')

        btn = tk.Button(
            lbl_f, text='All in One = Update + Show Profit', state='disabled',
            command=lambda:
            [
                self.stocks_update_click(),
                self.bank_trader_click(),
                self.profit_click(),
                Application.portfolio.update_history_data()

            ]
        )

        btn.pack(side='left')

        btn_lbl = tk.Label(lbl_f, text='Idle')  # creating progress label
        btn_lbl.pack(side='left')

        return btn, btn_lbl

    def root_binds(self):
        self.LOG.debug('Set keyboard bind keys')
        root.bind('<Control-e>', lambda event: self.fancy_click())
        root.bind('<Control-u>', lambda event: self.stocks_update_click())
        root.bind('<Control-b>', lambda event: self.bank_trader_click())
        root.bind('<Control-p>', lambda event: self.profit_click())
        root.bind('<Control-h>', lambda event: self.stats_click())
        root.bind('<Control-s>', lambda event: self.view_stocks_click())

    def active_window(self, window, is_root: bool = False):
        """setting windows as active windows when opened"""
        self.LOG.debug(f'Set currently active window [window={window.title}, is_root={is_root}]')
        window.lift()
        window.focus_force()
        window.grab_set()
        window.bind('<Escape>', lambda event: window.destroy())

    ##############################################################################################

    def file_menu(self):
        self.LOG.debug('Create file menu')
        file = tk.Menu(self.menu_bar, tearoff=0)
        file.add_command(label='Exit', command=root.quit, accelerator='Esc')
        self.menu_bar.add_cascade(label='File', menu=file)
        return file

    ##############################################################################################

    def state_normal(self):
        self.LOG.debug('Set state normal to menus')
        self.menu_bar.entryconfig('Edit', state='normal')
        self.menu_bar.entryconfig('View', state='normal')
        self.menu_bar.entryconfig('Graphs', state='normal')
        self.tools.entryconfig('Change Email Address', state='normal')
        self.all_in_one_btn.configure(state='normal')

        if self.portfolio.db.user_info.get_user_email_address():
            self.tools.entryconfig('Send Email Report', state='normal')

    def load_portfolio(self):
        self.LOG.debug('Loading database')
        self.progress_lbl_mode(process=True)

        Application.portfolio = MyFinanceManager()
        self.assets_info.configure(text=Application.portfolio.df_assets(to_email=True, plain_text=True))
        self.bottom_bar(Application.portfolio.db.last_modified.get_all())
        self.state_normal()
        Application.save_flag = True
        self.progress_lbl_mode(process=False)

    ##############################################################################################

    def edit_menu(self):
        self.LOG.debug('Creating edit menu')
        edit = tk.Menu(self.menu_bar, tearoff=0)
        edit.add_command(label='Add Stocks', command=self.add_stocks_click)
        edit.add_command(label='Remove Stock', command=self.remove_click)
        edit.add_command(label='Update Stocks Prices', accelerator='Ctrl+U', command=self.stocks_update_click)
        edit.add_command(label='Update Bank & Trader Cash Flow', accelerator='Ctrl+B', command=self.bank_trader_click)
        self.menu_bar.add_cascade(label='Edit', menu=edit, state='disabled')
        return edit

    ##############################################################################################

    def remove_click(self):
        def chosen_item():
            selected_symbol = list_box.get('active')
            symbol_name = selected_symbol.split(' - ')[0]
            self.LOG.debug(f'Trying to remove chosen stock - {symbol_name}')

            if symbol_name in len(Application.portfolio.db.stocks.get_stocks_names()):
                selected_amount = simpledialog.askinteger('System',
                                                          f'Enter amount to remove from {symbol_name}',
                                                          initialvalue=1, minvalue=1,
                                                          maxvalue=amount_dict[symbol_name]
                                                          )

                if selected_amount:
                    self.progress_lbl_mode(process=True)

                    Application.portfolio.remove_stock(symbol_name, int(selected_amount))
                    self.bottom_bar(Application.portfolio.db.last_modified.get_all())
                    self.assets_info.configure(text=Application.portfolio.df_assets(to_email=True, plain_text=True))
                    top.destroy()

                    self.progress_lbl_mode()

        top = self.create_top_level(title='Remove Stock')

        scrollbar = tk.Scrollbar(top, orient='vertical')

        list_box = tk.Listbox(top, yscrollcommand=scrollbar.set)

        scrollbar.configure(command=list_box.yview)
        scrollbar.pack(side='right', fill='y')

        list_box.pack(side='left', fill='both', expand=1)
        list_box.insert('end', 'Choose Symbol From List')
        list_box.selection_set(0)

        for stock in Application.portfolio.stocks_names:
            amount_dict = Application.portfolio.df_stocks().groupby(by=['Symbol']).sum().Amount.to_dict()
            list_box.insert('end', stock + f' - {amount_dict[stock]} shares')

        list_box.bind('<Button-1>', lambda event: chosen_item())

    def bank_trader_click(self):
        """for web scrap cash flows with bank Otsar Hahayal and Meitav Dash"""
        self.LOG.debug('Clicked on update bank trader')
        self.progress_lbl_mode(process=True)

        bank_cf, bank_usd_val = get_bank_info(mfm_output=True)
        Application.portfolio.update_bank_trader_foreign_currency('USD', u_bank_usd_val=bank_usd_val)
        trader_cf, self.days_left, trader_usd_val = get_trader_info(mfm_output=True)
        Application.portfolio.update_bank_trader_foreign_currency('USD', u_trader_usd_val=trader_usd_val)

        Application.portfolio.update_bank_trader_cf(u_bank_cf=bank_cf,
                                                    u_trader_cf=trader_cf)
        Application.save_flag = True
        self.assets_info.configure(text=Application.portfolio.df_assets(to_email=True, plain_text=True))
        self.bottom_bar(Application.portfolio.db.last_modified.get_all())

        self.progress_lbl_mode()
        messagebox.showinfo('System Message', 'Cash flows updated')

    def manual_bank_trader_click(self, all_mode: bool = False):
        """For manual enter cash flows"""
        self.LOG.debug('Clicked on bank trader update')

        top = self.create_top_level(title='', geometry='139x122')

        lbl1 = tk.Label(top, text='Bank Cash Flow')
        lbl1.pack()

        bank_cf = tk.Entry(top, justify='center')
        bank_cf.insert(0, Application.portfolio.bank_cf)
        bank_cf.focus_set()
        bank_cf.selection_range(0, 'end')
        bank_cf.pack()

        lbl2 = tk.Label(top, text='Trader Cash Flow')
        lbl2.pack()

        trader_cf = tk.Entry(top, justify='center')
        trader_cf.insert(0, Application.portfolio.trader_cf)
        trader_cf.pack()

        def submit_click():
            self.LOG.debug("Submit changing manually bank trader cash flow")
            Application.portfolio.update_bank_trader_cf(
                u_bank_cf=float(Calculator.evaluate(bank_cf.get())),
                u_trader_cf=float(Calculator.evaluate(trader_cf.get()))
            )

            Application.save_flag = True
            self.assets_info.configure(text=Application.portfolio.df_assets(to_email=True, plain_text=True))
            self.bottom_bar(Application.portfolio.db.last_modified.get_all())
            top.destroy()

        var = tk.IntVar()
        submit = tk.Button(top, text='Submit', command=lambda: [var.set(1), submit_click()])
        submit.pack()

        if all_mode:
            var = tk.IntVar()
            submit.wait_variable(var)

    def add_stocks_click(self):
        self.LOG.debug('Clicked on add stocks')
        counter = simpledialog.askinteger('System Message', 'How many stocks?', initialvalue=1, minvalue=1)
        if counter is None:
            return

        else:
            def stock_form():
                top = self.create_top_level(title='Add New Stock', geometry='258x185')

                def example_window():
                    example_win = self.create_top_level(title='Example Form', geometry='260x220')

                    photo = ImageTk.PhotoImage(Image.open(Application.EXAMPLE_FORM))

                    lbl = tk.Label(example_win, image=photo)
                    lbl.image = photo
                    lbl.pack()

                tk.Label(top, text="Symbol").grid(row=0, column=0)
                tk.Label(top, text="Date").grid(row=1, column=0)
                tk.Label(top, text="Amount").grid(row=2, column=0)
                tk.Label(top, text="Buy Price").grid(row=3, column=0)
                tk.Label(top, text="Currency").grid(row=4, column=0)
                tk.Label(top, text="Fund Number\n"
                                   "(For Israeli Stocks)").grid(row=5, column=0)

                example_btn = tk.Button(top, text='See Example', command=example_window)
                example_btn.grid(row=6, column=0)

                symbol = tk.Entry(top)
                symbol.grid(row=0, column=1)
                symbol.focus_set()

                date = tk.Entry(top)
                date.insert(0, 'Today')
                date.grid(row=1, column=1)

                amount = tk.Entry(top)
                amount.grid(row=2, column=1)

                buy_price = tk.Entry(top)
                buy_price.grid(row=3, column=1)

                lbl_og = tk.StringVar(top)
                lbl_og.set('Select')
                currency = tk.OptionMenu(top, lbl_og, *{'USD', 'ILS'})
                currency.grid(row=4, column=1)

                fund_num_exchange = tk.Entry(top)
                fund_num_exchange.grid(row=5, column=1)
                fund_num_exchange.insert(0, '0')

                def clicked():
                    self.LOG.debug('Clicked on adding new stock')
                    try:
                        s, d, a, b, c, f = symbol.get(), date.get(), int(amount.get()), float(buy_price.get()), \
                                           lbl_og.get(), int(fund_num_exchange.get())
                        Application.portfolio.add_stock(s, d, a, b, c, f)
                        Application.save_flag = False
                        self.assets_info.configure(text=Application.portfolio.df_assets(to_email=True,
                                                                                        plain_text=True))

                    except Exception as e:
                        messagebox.showinfo('System Message', 'Error in adding stock, see example form', icon='error')
                        self.LOG.exception('Error in adding stock', e)
                        raise

                    finally:
                        top.destroy()

                global submit_btn
                submit_btn = ttk.Button(
                    top, text="Submit",
                    command=lambda:
                    [
                        var.set(1),
                        clicked()
                    ]
                )

                submit_btn.grid(row=6, column=1, sticky='w')

            for i in range(1, counter + 1):
                var = tk.IntVar()
                stock_form()
                submit_btn.wait_variable(var)

            messagebox.showinfo('System Message', 'All stocks added')

    def stocks_update_click(self):
        self.LOG.debug('Clicked on stocks update')

        self.progress_lbl_mode(process=True)

        Application.portfolio.update_stocks_price()
        Application.save_flag = False
        self.assets_info.configure(text=Application.portfolio.df_assets(to_email=True, plain_text=True))
        self.bottom_bar(Application.portfolio.db.last_modified.get_all())
        messagebox.showinfo('System Message', 'All stocks prices updated')

        self.progress_lbl_mode()

    ##############################################################################################

    def view_menu(self):
        self.LOG.debug('Creating view menu')
        view = tk.Menu(self.menu_bar, tearoff=0)
        view.add_command(label='Stocks In Portfolio', command=self.view_stocks_click, accelerator='Ctrl+S')
        view.add_command(label='Portfolio History Stats', command=self.stats_click, accelerator='Ctrl+H')
        self.menu_bar.add_cascade(label='View', menu=view, state='disabled')
        return view

    ##############################################################################################

    def view_stocks_click(self):
        self.LOG.debug('Clicked on view stocks')
        try:
            html = Application.portfolio.df_stocks(to_email=True)

            top = self.create_top_level(title='Stocks In Portfolio', geometry='550x235')

            hf = HtmlFrame(top)
            hf.pack()
            hf.set_content(html)

        except AttributeError:
            messagebox.showinfo('System Message', 'No stocks to show', icon='error')
            self.LOG.exception('No stocks to show in view stocks')
            raise

    def stats_click(self):
        self.LOG.debug('Clicked on show stats')
        try:
            html = Application.portfolio.df_history(tabulate_output=True)

            top = self.create_top_level(title='Portfolio History Stats', geometry='650x400')

            hf = HtmlFrame(top)
            hf.pack()
            hf.set_content(html)

        except AttributeError:
            messagebox.showinfo('System Message', 'No history stats to show', icon='error')
            self.LOG.exception('No history to show in stats')
            raise

    ##############################################################################################

    def graphs_menu(self):
        self.LOG.debug('Creating graphs menu')
        graphs = tk.Menu(self.menu_bar, tearoff=0)
        graphs.add_command(label='Portfolio Profit', accelerator='Ctrl+P', command=self.profit_click)
        graphs.add_command(label='Portfolio Market Value', command=self.market_val_click)
        graphs.add_command(label='View Archived Graphs', command=self.older_graphs_click)
        self.menu_bar.add_cascade(label='Graphs', menu=graphs, state='disabled')
        return graphs

    ##############################################################################################

    def older_graphs_click(self):
        self.LOG.debug('Show older graphs clicked')
        list_of_files = glob(Application.portfolio.graphs_save_path + '/*.png')
        files_dict = {}
        for file in list_of_files:
            file_date = re.findall('\d{1,2}-\d{1,2}-\d{4}', file)[0]

            if file_date in files_dict.keys():
                files_dict[file_date].append(file)

            else:
                files_dict[file_date] = [file]

        def create_list(user_date):
            self.LOG.debug('Creating older graphs list')
            for date, files_list in files_dict.items():
                if date == user_date:
                    photo1 = ImageTk.PhotoImage(Image.open(files_list[0]))
                    photo2 = ImageTk.PhotoImage(Image.open(files_list[1]))
                    photo3 = ImageTk.PhotoImage(Image.open(files_list[2]))

                    lbl1.configure(image=photo1)
                    lbl1.image = photo1
                    lbl2.configure(image=photo2)
                    lbl2.image = photo2
                    lbl3.configure(image=photo3)
                    lbl3.image = photo3

        top = self.create_top_level(title='View Archived Graphs', geometry='1110x580')

        lbl_og = tk.StringVar(top)
        lbl_og.set('Select Date')
        sorted_dates = sorted(files_dict.keys(),
                              key=lambda x: datetime.datetime.strptime(x, '%d-%m-%Y'),
                              reverse=True)
        popup_menu = tk.OptionMenu(top, lbl_og, *sorted_dates, command=create_list)
        popup_menu.pack(side='top')

        tab_control = ttk.Notebook(top)
        tab1 = tk.Frame(tab_control)
        tab2 = tk.Frame(tab_control)
        tab3 = tk.Frame(tab_control)

        tab_control.add(tab1, text='Market Value ILS')
        tab_control.add(tab2, text='Profit ILS')
        tab_control.add(tab3, text='Profit Percentage')

        lbl1 = tk.Label(tab1, text='Select Date from list to display graph')
        lbl2 = tk.Label(tab2, text='Select Date from list to display graph')
        lbl3 = tk.Label(tab3, text='Select Date from list to display graph')

        lbl1.pack()
        lbl2.pack()
        lbl3.pack()

        tab_control.pack(fill="both", expand="yes")

        last_graphs = list(files_dict.keys())[-1]
        create_list(last_graphs)  # show last graphs created when opening.

        top.bind('<Left>', lambda event: tab_control.focus_set())
        top.bind('<Right>', lambda event: tab_control.focus_set())

    def profit_click(self):
        self.LOG.debug('Profit graph clicked')
        try:
            if len(Application.portfolio.db.stocks.get_stocks_names()) > 0:
                filename1 = Application.portfolio.graph(profit_numbers=True, save_only=True)
                photo1 = ImageTk.PhotoImage(Image.open(filename1))

                filename2 = Application.portfolio.graph(profit_percentage=True, save_only=True)
                photo2 = ImageTk.PhotoImage(Image.open(filename2))

                top = self.create_top_level(title='Profit Graphs', geometry='1000x530')

                tab_control = ttk.Notebook(top)
                tab1 = tk.Frame(tab_control)
                tab2 = tk.Frame(tab_control)

                tab_control.add(tab1, text='Numbers')
                tab_control.add(tab2, text='Percentage')

                lbl1 = tk.Label(tab1, image=photo1)
                lbl1.image = photo1

                lbl2 = tk.Label(tab2, image=photo2)
                lbl2.image = photo2

                lbl1.pack()
                lbl2.pack()

                tab_control.pack(fill="both", expand="yes")

                top.bind('<Left>', lambda event: tab_control.focus_set())
                top.bind('<Right>', lambda event: tab_control.focus_set())

            else:
                messagebox.showinfo('System Message', 'No stocks to show', icon='error')
                self.LOG.exception('No stocks to show in profit graph')

        except AttributeError:
            messagebox.showinfo('System Message', 'No stocks to show', icon='error')
            self.LOG.exception('No stocks to show in profit graph')

    def market_val_click(self):
        self.LOG.debug('Market val graph clicked')
        try:
            if len(Application.portfolio.db.stocks.get_stocks_names()) > 0:
                filename1 = Application.portfolio.graph(market_value=True, save_only=True)
                photo1 = ImageTk.PhotoImage(Image.open(filename1))

                top = self.create_top_level(title='Market Value Graph', geometry='1000x530')

                tab_control = ttk.Notebook(top)
                tab1 = tk.Frame(tab_control)

                tab_control.add(tab1, text='Numbers')

                lbl1 = tk.Label(tab1, image=photo1)
                lbl1.image = photo1

                lbl1.pack()

                tab_control.pack(fill="both", expand="yes")

                top.bind('<Left>', lambda event: tab_control.focus_set())
                top.bind('<Right>', lambda event: tab_control.focus_set())

            else:
                messagebox.showinfo('System Message', 'No stocks to show', icon='error')
                self.LOG.exception('No stocks to show in market val graph')

        except AttributeError:
            messagebox.showinfo('System Message', 'No stocks to show', icon='error')
            self.LOG.exception('No stocks to show in market val graphs')

    ##############################################################################################

    def tools_menu(self):
        self.LOG.debug('Tools menu created')
        tools = tk.Menu(self.menu_bar, tearoff=0)
        email = tk.Menu(tools, tearoff=0)
        email.add_command(label='Fancy Style', accelerator='Ctrl+E', command=self.fancy_click, state='normal')
        tools.add_cascade(label='Send Email Report', menu=email, state='disabled')
        tools.add_command(label='Currency Converter', command=self.converter_click)
        tools.add_command(label='Change Email Address', command=self.change_email, state='disabled')
        self.menu_bar.add_cascade(label='Tools', menu=tools)
        return tools

    ##############################################################################################

    def converter_click(self):
        self.LOG.debug('Converter clicked')

        def convert():
            if len(e1.get()) == 3 and len(e2.get()) == 3:

                try:
                    c_symbol = MyFinanceManager.currency_converter(symbol=e2.get())
                    c_result = MyFinanceManager.currency_converter(e1.get(), e2.get(),
                                                                   float(Calculator.evaluate(e1a.get())
                                                                         )
                                                                   )

                    if float(e1a.get()) == 0:
                        lbl.configure(text=f'0 {c_symbol}')

                    else:
                        lbl.configure(text=f'{c_result:,.2f} {c_symbol}')

                except:
                    pass

        top = self.create_top_level(title='Currency Converter', geometry='275x230')

        lf1 = tk.LabelFrame(top)
        lf1.pack()

        have = tk.Label(lf1, text='I Have', font=('Ariel Bold', 16))
        have.pack()

        e1 = tk.Entry(lf1, font=('Ariel', 16), justify='center')
        e1.pack()
        e1.focus_set()
        e1.insert(0, 'USD')

        e1a = tk.Entry(lf1, font=('Ariel', 16), justify='center')
        e1a.pack()
        e1a.insert(0, '1')

        lf2 = tk.LabelFrame(top)
        lf2.pack()

        want = tk.Label(lf2, text='I Want', font=('Ariel Bold', 16), justify='center')
        want.pack()

        e2 = tk.Entry(lf2, font=('Ariel', 16), justify='center')
        e2.pack()
        e2.insert(0, 'ILS')

        lbl = tk.Label(top, text='0', font=('Ariel Bold', 20), fg='red', justify='center')
        lbl.pack()

        convert()  # for first conversion to appear.

        currencies = ['EUR', 'IDR', 'BGN', 'ILS', 'GBP', 'DKK', 'CAD', 'JPY', 'HUF', 'RON', 'MYR', 'SEK', 'SGD',
                      'HKD', 'AUD', 'CHF', 'KRW', 'CNY', 'TRY', 'HRK', 'NZD', 'THB', 'USD', 'NOK', 'RUB', 'INR',
                      'MXN', 'CZK', 'BRL', 'PLN', 'PHP', 'ZAR']

        lbl_pm = tk.StringVar(top)
        lbl_pm.set('Currencies Available')
        popup_menu = tk.OptionMenu(top, lbl_pm, *{val for val in currencies})
        popup_menu.pack(side='left')

        top.bind('<KeyRelease>', lambda event: convert())
        top.bind('<Button-1>', lambda event: lbl_pm.set('Currencies Available'))

    def fancy_click(self):
        self.LOG.debug('Fancy email clicked')
        self.progress_lbl_mode(process=True)

        receiver_email = Application.portfolio.db.user_info.get_user_email_address()
        Application.portfolio.send_fancy_email(receiver_email=receiver_email)

        messagebox.showinfo('System Message', 'Email sent successfully')
        self.progress_lbl_mode()

    def change_email(self):
        self.LOG.debug('Change email clicked')
        new_email = simpledialog.askstring('Change Email Address', 'Please Type New Address')
        if new_email is None:
            return

        self.portfolio.db.user_info.change_email_address(new_email)
        self.state_normal()
        self.bottom_bar(Application.portfolio.db.last_modified.get_all())

    ##############################################################################################

    def help_menu(self):
        self.LOG.debug('Creating Help menu')
        help_m = tk.Menu(self.menu_bar, tearoff=0)
        help_m.add_command(label='About', command=self.about_click)
        self.menu_bar.add_cascade(label='Help', menu=help_m)
        return help_m

    ##############################################################################################

    def about_click(self):
        self.LOG.debug('About clicked')
        top = self.create_top_level(title='About', geometry='215x220')
        tk.Label(
            top, text='\n\nMyFinanceManager 2019\n\n\n'
                      'Powered by Python % MongoDB\n\n\n'
                      'Ofek Saar\n'
                      'ofekip@gmail.com'
        ).pack()

    ##############################################################################################


if __name__ == "__main__":
    root = tk.Tk()
    root.title('MyFinanceManager')
    root.geometry('585x395')
    app = Application(parent=root)
    app.mainloop()
