# import libraries
import pandas as pd
import tkinter as tk
from tkinter import ttk,messagebox
from tkinter.messagebox import showinfo
import random
import smtplib
from email.message import EmailMessage
import ssl
import os
from dotenv import load_dotenv
from datetime import date
from PIL import Image, ImageTk



# define variables
root_color = "#FFB200"
title_font = ("Sans Serif", 32, "bold")
subtitle_font = ("Sans Serif", 8)
subsubtitle_font = ("Sans Serif", 10)

# define classes for each page of application
class tkinterApp(tk.Tk):

    # __init__ function for class tkinterApp
    def __init__(self, database, *args, **kwargs):
        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)
        ico = Image.open('icon.png')
        photo = ImageTk.PhotoImage(ico)
        self.wm_iconphoto(False, photo)
        self.title("Cooking")
        self.state('zoomed') 
        self.protocol("WM_DELETE_WINDOW",self.on_exit)

        # define button style
        s = ttk.Style()
        s.theme_use("alt")
        s.configure("my.TButton", font=("Sans Serif", 10),foreground="#FFFFFF", background="#000000",focuscolor='none',weight=30, height=10)

        # create container
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # initialize frames to an empty array
        self.frames = {}
        self.database = database

        # iterate through a tuple of the different pages
        for F in (StartPage, MenuPage, RoulettePage, EntryPage):

            frame = F(parent=container, controller=self)

            # initialize frame of that object
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    # function to display the current frame
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()
    
    # function to execute on eit
    def on_exit(self):
        if messagebox.askyesno("EXIT","DO YOU WANT TO OVERWRITE THE EXCEL FILE?"):
            today = date.today()
            self.database.loc[self.database['Dish'].isin (self.frames[MenuPage].output_list),"When?"]=today
            delta= pd.Timestamp.now().normalize() -  pd.to_datetime(self.database["When?"])
            self.database["Days ago?"]= delta.dt.days+1
            self.database.to_excel("recipes.xlsx", index=False)
            self.destroy()
        else:
            self.destroy()


class StartPage(tk.Frame):
    def __init__(self, parent, controller, **kwargs):

        tk.Frame.__init__(self, parent, background=root_color)

        #create some butons and text
        self.label_subtitle = ttk.Label(
            self,
            text="COOKING MENU RECOMMENDATION SYSTEM",
            font=subtitle_font,
            background=root_color,
        )       
        self.label_subtitle.place(relx=0.1, rely=0.20, anchor='w')

        self.label_title = ttk.Label(
            self,
            text="Let's cook together",
            font=title_font,
            background=root_color,
        )
        self.label_title.place(relx=0.1, rely=0.25, anchor='w')

        self.label_subsubtitle = ttk.Label(
            self,
            text="This application can help you create perfectly balanced weekly menu.\nThe idea is simple, the longer you haven't eaten pizza, the more likely you are to eat it this week:)\nEvery time you confirm the menu, you will also receive an e-mail notification with the recipes.\nIn the 'MENU' section you can see the proposed menufor this week. If you wish to make any changes, feel free to do so.\n'ROULETTE' section lets you draw random dish from a database.\nIf you would like to add new recipe to the database, go to 'NEW ENTRY' section",
            font=subsubtitle_font,
            background=root_color,
        )
        self.label_subsubtitle.place(relx=0.1, rely=0.4, anchor='w')

        self.button_menu = ttk.Button(
            self,
            text="MENU",
            style="my.TButton",
            command=lambda: controller.show_frame(MenuPage),
        )
        self.button_menu.place(relx=0.1, rely=0.60, anchor='w')

        self.button_roulette = ttk.Button(
            self,
            text="ROULETTE",
            style="my.TButton",
            command=lambda: controller.show_frame(RoulettePage),
        )
        self.button_roulette.place(relx=0.1, rely=0.65, anchor='w')

 
        self.button_entry = ttk.Button(
            self,
            text="NEW ENTRY",
            style="my.TButton",
            command=lambda: controller.show_frame(EntryPage),
        )
        self.button_entry.place(relx=0.1, rely=0.70, anchor='w')


class MenuPage(tk.Frame):
    def __init__(self, parent, controller, **kwargs):

        tk.Frame.__init__(self, parent, background=root_color)

        self.controller=controller

        self.label_menu = ttk.Label(self, text="Menu", font=title_font, background=root_color)
        self.label_menu.grid(row=0, column=1, padx=10, pady=10)

        self.label_description = ttk.Label(self,  text="THIS WEEK'S MENU",
              font=subsubtitle_font, background=root_color)
        self.label_description.grid(row=1, column=1, padx=10, pady=10)

        # Database transformations needed to run algorithm
        self.df=self.controller.database.copy()
        self.df['Dish']= self.df['Dish'].astype(str) 
        self.df['Add-ons?']= self.df['Add-ons?'].astype(str)    
        self.df['Vege?']= self.df['Vege?'].replace(["Tak","Nie"],[1,0])
        self.df['Vege?']= self.df['Vege?'].astype('int')


        # "Algorithm" to select recipes 
        self.algorithm()

        self.button_reroll = ttk.Button(
            self,
            text="REROLL",
            style="my.TButton", 
            command=lambda: self.algorithm(),
        )
        self.button_reroll.grid(row=9, column=1, padx=10, pady=10)

        self.button_accept = ttk.Button(
            self,
            text="ACCEPT",
            style="my.TButton",
            command=lambda: self.accept_send_mail()
        )
        self.button_accept.grid(row=8, column=1, padx=10, pady=10)


        self.button_back = ttk.Button(
            self,
            text="BACK",
            style="my.TButton",
            command=lambda: controller.show_frame(StartPage),
        )
        self.button_back.grid(row=10, column=1, padx=10, pady=10)

    
    def algorithm(self):
        while True:
            self.output_list=[]
            self.df_list=[self.df]
            self.servings_list=[]
            self.vege_list=[]
            for i in range(4):
                self.out_new,self.df_new, self.servings_new,self.vege_new=losuj(self.df_list[i])
                self.df_list.insert(i+1,self.df_new)
                self.output_list.insert(i,self.out_new)
                self.servings_list.insert(i, self.servings_new)
                self.vege_list.insert(i, self.vege_new)

            if (sum(self.servings_list)==7) & (sum(self.vege_list)>=1):
                break
            else:
                pass


        for i, row in zip(range(len(self.output_list)),range(3,len(self.output_list)+3)):
            if f'label_menu{i}' in globals():   
                globals()[f'label_menu{i}'].config(text="")
            globals()[f'label_menu{i}']= ttk.Label(self,  text="{}".format(self.output_list[i]),font=subtitle_font, background=root_color)
            globals()[f'label_menu{i}'].grid(row=row, column=1, padx=10, pady=10)
            globals()[f'options_menu{i}']= tk.StringVar(self)
            globals()[f'options_menu{i}'].set(self.output_list[i])
            globals()[f'opt_menu{i}']=tk.OptionMenu(self, globals()[f'options_menu{i}'], *self.df_list[i].Dish.values.tolist())
            globals()[f'opt_menu{i}'].grid(row=row,column=1)
            globals()[f'opt_menu{i}'].grid_forget()          
            globals()[f'button_edit_menu{i}']= ttk.Button(
            self,
            text="Edit",
            style="my.TButton",
            command=lambda i=i, row=row: self.edit(widget_out=globals()[f'label_menu{i}'], button_out=globals()[f'button_edit_menu{i}'], widget_in=globals()[f'opt_menu{i}'], button_in=globals()[f'button_save_menu{i}'], row=row),
            )
            globals()[f'button_save_menu{i}']= ttk.Button(
            self,
            text="Save",
            style="my.TButton",
            command=lambda i=i, row=row: self.save(entry=globals()[f'options_menu{i}'],i=i, widget_out=globals()[f'opt_menu{i}'], button_out=globals()[f'button_save_menu{i}'], widget_in=globals()[f'label_menu{i}'], button_in=globals()[f'button_edit_menu{i}'], row=row),
            )
            globals()[f'button_edit_menu{i}'].grid(row=row, column=2, padx=10, pady=10)
            globals()[f'button_save_menu{i}'].grid(row=row, column=2, padx=10, pady=10)
            globals()[f'button_save_menu{i}'].grid_forget()
    

    def edit(self,widget_out, button_out, widget_in, button_in, row):
        widget_out.grid_forget()
        button_out.grid_forget()
        widget_in.grid(row=row,column=1)
        button_in.grid(row=row, column=2, padx=10, pady=10)


    def save(self, entry,i,widget_out, button_out, widget_in, button_in, row):
        content = entry.get()
        self.output_list[i]=content
        widget_out.grid_forget()
        button_out.grid_forget()
        widget_in.config(text="{}".format(self.output_list[i]))
        widget_in.grid(row=row,column=1)
        button_in.grid(row=row, column=2, padx=10, pady=10)


    def accept_send_mail(self):
        
        if messagebox.askyesno("EXIT","ARE YOU SURE YOU WANT TO ACCEPT THE MENU AND SEND AN EMAIL?"):
            load_dotenv()

            # email authorization via .env file
            email_address=os.getenv("EMAIL_ADDRESS")
            email_password=os.getenv("EMAIL_PASSWORD")
            email_receiver=os.getenv("EMAIL_RECEIVER")

            # create email
            msg = EmailMessage()
            msg['Subject'] = "WEEKLY MENU"
            msg['From'] = email_address
            msg['To'] = email_receiver
            self.links_list=[]
            for i in range(4):
                link=self.df[self.df["Dish"]==self.output_list[i]]['Link?'].item()
                self.links_list.append(link)
            msg.set_content("The menu for this week is:\n1) {}: {}\n2) {}: {}\n3) {}: {}\n4) {}: {}".format(self.output_list[0],self.links_list[0],self.output_list[1],self.links_list[1],self.output_list[2],self.links_list[2],self.output_list[3], self.links_list[3]))

            context = ssl.create_default_context()

            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(email_address, email_password)
                smtp.sendmail(email_address, email_receiver, msg.as_string())
            
            self.destroy()

        
class RoulettePage(tk.Frame):
    def __init__(self, parent, controller, **kwargs):

        tk.Frame.__init__(self, parent, background=root_color)
        
        self.controller=controller
        
        self.label = ttk.Label(self, text="Roulette", font=title_font, background=root_color)
        self.label.grid(row=1, column=0,padx=10, pady=10)


        self.button_roll = ttk.Button(
            self,
            text="ROLL THE RECIPE",
            style="my.TButton",
            command=lambda: self.roll_recipe(),
        )
        self.button_roll.grid(row=2,column=0,padx=10, pady=10)

        self.button_back = ttk.Button(
            self,
            text="BACK",
            style="my.TButton",
            command=lambda: controller.show_frame(StartPage),
        )
        self.button_back.grid(row=3, column=0,padx=10, pady=10)

    def roll_recipe(self):
        output=random.choice(self.controller.database.Dish.to_list())
        showinfo(
            title='INFORMATION',
            message=f'The recipe for today is {output}'
        )



class EntryPage(tk.Frame):
    def __init__(self, parent, controller, **kwargs):
        self.controller = controller

        tk.Frame.__init__(self, parent, background=root_color)
        label = ttk.Label(self, text="Entry", font=title_font, background=root_color)
        label.grid(row=0, column=1, columnspan=6, padx=10, pady=10)

        # Treeview
        self.cols = self.controller.database.columns
        self.trv = ttk.Treeview(self, selectmode="browse", show="headings", columns=tuple(self.cols))
        self.trv.grid(row=1, column=1, columnspan=6, padx=20, pady=20)

        # Add column names
        for col, i in zip(self.cols, range(len(self.cols))):
            self.trv.column(i, width=80, anchor="c")
            self.trv.heading(i, text=col)

        # Insert rows from df
        for i in range(len(self.controller.database)):
            self.trv.insert("", "end", iid=i, values=self.controller.database.loc[i, :].values.flatten().tolist())

        # Labels to get row data
        self.l0 = tk.Label(self,  text='Record entry',
              font=subsubtitle_font, width=30,anchor="c", bg=root_color)  
        self.l0.grid(row=2,column=1,columnspan=6) 

        self.l1 = tk.Label(self,  text='Dish?', width=10,anchor="c")  
        self.l1.grid(row=3,column=3) 
        self.t1 = tk.Text(self,  height=1, width=10,bg="white") 
        self.t1.grid(row=3,column=4)

        self.l2 = tk.Label(self,  text='Vege?', width=10,anchor="c")  
        self.l2.grid(row=4,column=1) 
        self.options2=tk.StringVar(self)
        self.options2.set("")
        self.o2=tk.OptionMenu(self, self.options2, "Tak","Nie")
        self.o2.grid(row=4,column=2)

        self.l3 = tk.Label(self,  text='Add-ons?', width=10,anchor="c")  
        self.l3.grid(row=4,column=3) 
        self.options3=tk.StringVar(self)
        self.options3.set("")
        self.o3=tk.OptionMenu(self, self.options3, "Ziemniaki","Makaron","Ryż/kasza","Inne")
        self.o3.grid(row=4,column=4)

        self.l4 = tk.Label(self,  text='Demanding?', width=10,anchor="c")  
        self.l4.grid(row=4,column=5) 
        self.options4=tk.StringVar(self)
        self.options4.set("")
        self.o4=tk.OptionMenu(self, self.options2, "Tak","Nie")
        self.o4.grid(row=4,column=6)

        self.l5 = tk.Label(self,  text='Days ago?', width=10,anchor="c")  
        self.l5.grid(row=5,column=1) 
        self.t5 = tk.Text(self,  height=1, width=10,bg="white") 
        self.t5.grid(row=5,column=2)
        self.t5.insert("1.0", "1")

        self.l6 = tk.Label(self,  text='Servings?', width=10,anchor="c")  
        self.l6.grid(row=5,column=3) 
        self.t6 = tk.Text(self,  height=1, width=10,bg="white") 
        self.t6.grid(row=5,column=4)
   
        self.l7 = tk.Label(self,  text='Link?', width=10,anchor="c")  
        self.l7.grid(row=5,column=5) 
        self.t7 = tk.Text(self,  height=1, width=10,bg="white") 
        self.t7.grid(row=5,column=6)


        button_add_row = ttk.Button(
            self,
            text="ADD NEW ROW",
            style="my.TButton",
            command=lambda: self.insert_row(),
        )
        button_add_row.grid(row=10, column=1, columnspan=6,padx=5, pady=5)


        button_edit_row = ttk.Button(
            self,
            text="EDIT ROW",
            style="my.TButton",
            command=lambda: self.edit_row(),
        )
        button_edit_row.grid(row=11, column=1,columnspan=5,padx=5, pady=5)
        
        button_save_row = ttk.Button(
            self,
            text="SAVE EDITED ROW",
            style="my.TButton",
            command=lambda: self.save_edited_row(),
        )
        button_save_row.grid(row=11, column=2,columnspan=5,padx=5, pady=5)

        button_delete_row = ttk.Button(
            self,
            text="DELETE ROW",
            style="my.TButton",
            command=lambda: self.delete_row(),
        )
        button_delete_row.grid(row=12, column=1,columnspan=6,padx=5, pady=5)

        button_back = ttk.Button(
            self,
            text="BACK",
            style="my.TButton",
            command=lambda: controller.show_frame(StartPage),
        )
        button_back.grid(row=13, column=1, columnspan=6,padx=5, pady=5)



    def insert_row(self):
        values=[]
        values.append(self.t1.get("1.0","end"))
        values.append(self.options2.get() )
        values.append(self.options3.get() )
        values.append(self.options4.get() )
        values.append(self.t5.get("1.0","end"))
        values.append(self.t6.get("1.0","end"))
        values.append(self.t7.get("1.0","end"))
        if self.t5.get("1.0","end")=="1\n":
            values.append(date.today())
        self.trv.insert("", "end", values=values)
        self.controller.database.loc[len(self.controller.database)]=values
        showinfo(
            title='INFORMATION',
            message=f'New recipe added succesfully!'
        )

    def edit_row(self):
        self.selected_item = self.trv.focus()
        item_details=self.trv.item(self.selected_item)
        values=item_details.get("values")
        self.t1.delete("1.0","end")
        self.t1.insert("1.0", values[0]) 
        self.options2.set(values[1])
        self.options3.set(values[2])
        self.options4.set(values[3])
        self.t5.delete("1.0","end")
        self.t5.insert("1.0",values[4])
        self.t6.delete("1.0","end")
        self.t6.insert("1.0",values[5])
        self.t7.delete("1.0","end")
        self.t7.insert("1.0",values[6])

    def save_edited_row(self):
        values=[]
        values.append(self.t1.get("1.0","end"))
        values.append(self.options2.get() )
        values.append(self.options3.get() )
        values.append(self.options4.get() )
        values.append(self.t5.get("1.0","end"))
        values.append(self.t6.get("1.0","end"))
        values.append(self.t7.get("1.0","end"))
        if self.t5.get("1.0","end")=="1\n":
            values.append(date.today())
        self.trv.item(self.selected_item,values=values)
        self.controller.database.loc[int(self.selected_item)]=values  

    def delete_row(self):
        if messagebox.askyesno("DELETE","Are you sure you want to delete this row?"):
            selected_item = self.trv.selection()[0]
            self.trv.delete(selected_item)
            self.controller.database=self.controller.database.drop(int(selected_item))




# define functions
def losuj(database):
    output=random.choices(database.Dish.to_list(),weights=database['Days ago?'].to_list())
    dodatek=database.loc[database['Dish']==output[0],'Add-ons?']
    servings=database.loc[database['Dish']==output[0],'Servings?'].item()
    vege=database.loc[database['Dish']==output[0],'Vege?'].item()
    database=database[database['Add-ons?']!=str(dodatek.item())]
    return output[0],database,servings, vege



if __name__ == "__main__":
    database = pd.read_excel("recipes.xlsx")
    app = tkinterApp(database=database)
    app.mainloop()


